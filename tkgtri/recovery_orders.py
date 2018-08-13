from tkgtri import core
from tkgtri import errors
from tkgtri import TradeOrder
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

        self.max_order_updates = 10

        self.order_command = None  # None, new, cancel

        if symbol is not None:
            self.side = core.get_trade_direction_to_currency(symbol, self.dest_currency)

        self.active_order = None  # .. TradeOrder

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

    def get_recovery_price_for_best_dest_amount(self):
        """
        :return: price for recovery order from target_amount and target_currency without fee
        """
        if self.best_dest_amount == 0 or self.start_amount == 0:
            raise errors.RecoveryManagerError("RecoveryManagerError: Zero start ot dest amount")

        if self.symbol is None:
            raise errors.RecoveryManagerError("RecoveryManagerError: Symbol is not set")

        if self.side is None:
            raise errors.RecoveryManagerError("RecoveryManagerError: Side not set")

        if self.side == "buy":
            return self.start_amount / self.best_dest_amount
        if self.side == "sell":
            return self.best_dest_amount / self.start_amount
        return False

    def create_recovery_order(self, price):
        order_params = (self.symbol, self.start_currency, self.start_amount, self.dest_currency, price)

        if False not in order_params:
            self.price = price
            order = TradeOrder.create_limit_order_from_start_amount(*order_params)
            self.active_order = order
            return order
        else:
            raise errors.RecoveryManagerError("Not all parameters for Order are set {}")

    def get_active_order(self):
        return self.active_order

    def update_from_exchange_data(self, resp, market_data=None):
        """
        :param resp:
        :param market_data:
        :return:

        """

        self.active_order.update_order_from_exchange_resp(resp)

        if self.state == "best_price":

            if self.active_order.status == "open":
                if self.active_order.update_requests_count >= self.max_order_updates \
                        and self.active_order.filled < self.active_order.amount:

                    self.order_command = "cancel"

            if self.active_order.status == "closed":
                self.state = "closed"
                # collect results
                pass

            if self.active_order.status == "canceled":
                self.state = "market_price"

                if market_data is not None:
                    new_price = market_data["price"]
                    self.active_order = self.create_recovery_order(new_price)
                    self.order_command = "new"
                else:
                    #raise RecoveryOrder("New price not set")
                    pass
        pass

    def check_aim(self):
        pass

