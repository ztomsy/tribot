from tkgtri import core
from tkgtri import errors
from tkgtri import TradeOrder
import copy
import uuid
from tkgtri import ccxtExchangeWrapper
from datetime import datetime

class OrderWithAim(object):
    pass


class RecoveryOrder(OrderWithAim):

    def __init__(self, symbol, start_currency: str, start_amount: float, dest_currency: str,
                 dest_amount: float = 0.0,
                 fee: float = 0.0):

        self.symbol = symbol
        self.start_currency = start_currency
        self.start_amount = start_amount
        self.dest_currency = dest_currency
        self.fee = fee
        self.best_dest_amount = dest_amount
        self.best_price = 0.0
        self.price = 0.0

        self.status = "new"  # open, open_cancel_order, open_new_order, closed
        self.state = "best_amount"  #  "market_price" for reporting purposes

        self.filled_dest_amount = 0.0
        self.filled_start_amount = 0.0
        self.filled_price = 0.0

        self.filled = 0.0  # filled amount of base currency
        self.amount = 0.0  # total expected amount of to be filled base currency

        self.max_order_updates = 10

        self.order_command = None  # None, new, cancel

        if symbol is not None:
            self.side = core.get_trade_direction_to_currency(symbol, self.dest_currency)
            if self.side == "buy":
                self.amount = self.best_dest_amount
            else:
                self.amount = self.start_amount

        self.active_order = None  # .. TradeOrder
        self.orders_history = list()

        self.market_data = dict()  # market data dict: {symbol : {price :{"buy": <ask_price>, "sell": <sell_price>}}

        self._prev_filled_dest_amount = 0.0   # filled amounts on previous orders
        self._prev_filled_start_amount = 0.0  # filled amounts on previous orders
        self._prev_filled = 0.0               # filled amounts on previous orders

        self.init_best_amount()



    # @property
    # def symbol(self):
    #     return self.__symbol
    #
    # # set the symbol and side of recovery order
    # @symbol.setter
    # def symbol(self, value):
    #     self.__symbol = value
    #     if value is not None:
    #         self.side = core.get_trade_direction_to_currency(value, self.dest_currency)

    def init_best_amount(self):
        price = self.get_recovery_price_for_best_dest_amount()
        self.active_order = self.create_recovery_order(price)
        self.status = "open"
        self.state = "best_amount"
        self.order_command = "new"

    def init_market_price(self):
        try:
            price = self.market_data[self.symbol]["price"][self.side]
        except Exception:
            raise errors.OrderError("Could not set price from market data")

        self.active_order = self.create_recovery_order(price)
        self.status = "open"
        self.state = "market_price"
        self.order_command = "new"

    def get_recovery_price_for_best_dest_amount(self):
        """
        :return: price for recovery order from target_amount and target_currency without fee
        """
        if self.best_dest_amount == 0 or self.start_amount == 0:
            raise errors.OrderError("RecoveryManagerError: Zero start ot dest amount")

        if self.symbol is None:
            raise errors.OrderError("RecoveryManagerError: Symbol is not set")

        if self.side is None:
            raise errors.OrderError("RecoveryManagerError: Side not set")

        if self.side == "buy":
            return self.start_amount / self.best_dest_amount
        if self.side == "sell":
            return self.best_dest_amount / self.start_amount
        return False

    def create_recovery_order(self, price):

        amount = self.start_amount - self.filled_start_amount

        if amount <= 0:
            raise errors.OrderError("Bad new order amount {}".format(amount))

        order_params = (self.symbol, self.start_currency, amount,
                        self.dest_currency, price)

        if False not in order_params:
            self.price = price
            order = TradeOrder.create_limit_order_from_start_amount(*order_params)
            return order
        else:
            raise errors.OrderError("Not all parameters for Order are set")

    def close_active_order(self):
        if self.active_order.status == "closed" or self.active_order.status == "canceled":
            self.orders_history.append(copy.copy(self.active_order))
            self.active_order = None
            self.order_command = ""

            self._prev_filled = copy.copy(self.filled)
            self._prev_filled_start_amount = copy.copy(self.filled_start_amount)
            self._prev_filled_dest_amount = copy.copy(self.filled_dest_amount)

        else:
            raise errors.OrderError("Active Trade order is not closed {}".format(self.active_order.status))

    # todo check if active_order is closed or cancelled
    def close_order(self):
        # self.close_active_order()
        self.status = "closed"
        self.active_order = None
        self.order_command = ""

    def get_active_order(self):
        return self.active_order

    def set_active_order(self, order: TradeOrder):
        self.active_order = order

    def update_from_exchange(self, resp, market_data=None):
        """
        :param resp:
        :param market_data: some market data (price, orderbook?) for new tradeOrder
        :return: updates the self.order_command

        """
        self.active_order.update_order_from_exchange_resp(resp)

        self.filled_dest_amount = self._prev_filled_dest_amount + self.active_order.filled_dest_amount
        self.filled_start_amount = self._prev_filled_start_amount + self.active_order.filled_start_amount

        if self.filled_dest_amount != 0 and self.filled_start_amount != 0:
            self.filled_price = self.filled_start_amount / self.filled_dest_amount if self.side == "buy" else \
                self.filled_dest_amount / self.filled_start_amount

        self.filled = self._prev_filled + self.active_order.filled

        if self.state == "best_amount" or self.state == "market_price":

            if self.active_order.status == "open":
                self.order_command = "hold"

                if self.active_order.update_requests_count >= self.max_order_updates \
                        and self.active_order.filled < self.active_order.amount:
                    self.order_command = "cancel"
                return self.order_command

            if self.active_order.status == "closed":
                self.order_command = ""
                self.close_active_order()
                self.close_order()
                return self.order_command

            if self.active_order.status == "canceled":
                self.close_active_order()

                if self.filled >= self.amount:  # close order if filled amount is OK
                    self.close_order()
                    return self.order_command

                self.state = "market_price"  # else set new order status
                if market_data is not None:
                    new_price = market_data["price"]
                    self.active_order = self.create_recovery_order(new_price)
                    self.order_command = "new"
                else:
                    raise errors.OrderError("New price not set")
                return self.order_command

        # if self.state == "market_price":
        #     if self.active_order.status == "open":
        #         self.order_command = "hold"
        #
        #         if self.active_order.update_requests_count >= self.max_order_updates \
        #                 and self.active_order.filled < self.active_order.amount:
        #             self.order_command = "cancel"
        #         return True
        #
        #     if self.active_order.status == "closed":
        #         self.order_command = "hold"
        #         self.close_active_order()
        #         self.close_order()
        #         return True
        #
        #     if self.active_order.status == "canceled":
        #         self.close_active_order()
        #         self.state = "market_price"
        #
        #         if market_data is not None:
        #             new_price = market_data["price"]
        #             self.active_order = self.create_recovery_order(new_price)
        #             self.order_command = "new"
        #         else:
        #             #raise RecoveryOrder("New price not set")
        #             pass
        #         return True

    def check_aim(self):
        pass

