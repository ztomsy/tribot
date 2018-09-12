from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
from tkgtri import OrderWithAim
from tkgtri import core
from datetime import datetime
from tkgtri import errors
from tkgtri.errors import *
import copy

class OwaManager(object):

    LOG_DEBUG = "DEBUG"
    LOG_INFO = "INFO"
    LOG_ERROR = "ERROR"
    LOG_CRITICAL = "CRITICAL"

    def __init__(self, exchange: ccxtExchangeWrapper, max_order_update_attempts=20, max_cancel_attempts=10):
        self.orders = list()

        self.max_order_update_attempts = max_order_update_attempts
        self.max_cancel_attempts = max_cancel_attempts

        self.last_update_time = datetime(1, 1, 1, 1, 1, 1, 1)

        self.orders = list()
        self._prev_orders_status = dict()  # dict of orders by id

        self.exchange = exchange
        self.supplementary = dict() # dict of supplementary data  as {"order_id": {dict of data}}

        self._last_update_closed_orders = list()  # closed orders from last update

    def _create_order(self, order:TradeOrder):
        if self.exchange.offline:
            self.exchange.add_offline_order_data(order, 3)

        results = None
        i = 0
        while bool(results) is not True and i < self.max_order_update_attempts:
            self.log(self.LOG_INFO, "creating order ateempt #{}".format(i))
            try:
                results = self.exchange.place_limit_order(order)
            except Exception as e:
                self.log(self.LOG_ERROR, type(e).__name__)
                self.log(self.LOG_ERROR, e.args)
                self.log(self.LOG_INFO, "retrying to create order...")
            i += 1

        return results

    def _update_order(self, order: TradeOrder):

        results = None
        self.log(self.LOG_INFO, "..updating trade order")
        try:
            results = self.exchange.get_order_update(order)
        except Exception as e:
            self.log(self.LOG_ERROR, "Could not update order")
            self.log(self.LOG_ERROR, type(e).__name__)
            self.log(self.LOG_ERROR, e.args)
            self.log(self.LOG_INFO, "retrying to get trades...")

        return results

    def _cancel_order(self, order: TradeOrder):
        return self.exchange.cancel_order(order)

    # blocking method !!!!!
    def cancel_order(self, trade_order):
        cancel_attempt = 0

        while trade_order.status != "canceled" and trade_order.status != "closed":
            cancel_attempt += 1
            try:
                self._cancel_order(trade_order)

            except Exception as e:
                self.on_order_update_error(e)

            finally:

                try:
                    resp = self._update_order(trade_order)
                    trade_order.update_order_from_exchange_resp(resp)
                except Exception as e1:
                    self.on_order_update_error(e1)

                if cancel_attempt >= self.max_cancel_attempts:
                    raise errors.OwaManagerCancelAttemptsExceeded("Cancel Attempts Exceeded")

        return True

    def log(self, level, msg, msg_list=None):
        if msg_list is None:
            print("{} {}".format(level, msg))
        else:
            print("{} {}".format(level, msg))
            for line in msg_list:
                print("{} ... {}".format(level, line))

    def _get_trade_results(self, order: TradeOrder):

        results = None
        i = 0
        while bool(results) is not True and i < self.max_order_update_attempts:
            self.log(self.LOG_INFO, "getting trades #{}".format(i))
            try:
                results = self.exchange.get_trades_results(order)
            except Exception as e:
                self.log(self.LOG_ERROR, type(e).__name__)
                self.log(self.LOG_ERROR, e.args)
                self.log(self.LOG_INFO, "retrying to get trades...")
            i += 1

        return results

    def add_order(self, order: OrderWithAim):
        self.orders.append(order)

    def get_order_by_uuid(self, uuid):
        pass

    def _update_order_from_exchange(self, order: OrderWithAim, resp, market_data=None):

        try:
            order.update_from_exchange(resp, market_data)
        except Exception as e:
            self.log(self.LOG_ERROR, type(e).__name__)
            self.log(self.LOG_ERROR, e.args)

    def get_open_orders(self):
        return list(filter(lambda x: x.status != "closed", self.orders))

    def get_order_by_id(self, id):
        o = (order for order in self.orders if order.id == id)
        return o

    def set_order_supplementary_data(self, order: OrderWithAim, data: dict):
        """
        Add supplementary data (as dict) for order. For reporting or other purposes. The data will be stored as
        supplementary[order.id] in order manager. This method will override previously stored data.
        :param data: dict of data
        :param order: order object reference
        :return: True
        """

        self.supplementary[order.id] = copy.copy(data)

        return True

    # call back when the OwaOrder is being closed
    def on_order_close(self, order):
        pass

    def proceed_orders(self):

        self._last_update_closed_orders = list()
        open_orders = list(filter(lambda x: x.status != "closed" and x.active_order is not None, self.orders))

        for order in open_orders:

            self._prev_orders_status[order.id] = copy.copy(order)

            self.log(self.LOG_INFO, "Order {} status: {}. State {}. Total filled {}/{}".format(
                order.id, order.status, order.state, order.filled, order.amount))

            if order.order_command == "new":
                self.log(self.LOG_INFO, "Order {} creating new trade order for {} -{}-> {} amount {} price {}".format(
                    order.id, order.start_currency, order.side, order.dest_currency, order.get_active_order().amount,
                    order.get_active_order().price))

                if order.get_active_order().status != "open":
                    resp = self._create_order(order.get_active_order())
                    if resp is None or (not "id" in resp):
                        self.log(self.LOG_ERROR, "Order {} could not create new trade order".format(order.id))
                    else:
                        self._update_order_from_exchange(order, resp)

                else:
                    raise OwaManagerError("Order already set")

            elif order.order_command == "hold":

                resp = self._update_order(order.get_active_order())

                if resp["status"] == "closed" or resp["status"] == "canceled":
                    self.log(self.LOG_INFO, "Order {} trade order have been closed  {} -{}-> {}".format(
                        order.id, order.start_currency, order.side, order.dest_currency))

                    # workaround.we should have updated order data before getting the correct trades results from trades
                    order.active_order.update_order_from_exchange_resp(resp)

                    if resp["filled"] > 0:

                        trades = self._get_trade_results(order.get_active_order())
                        if trades is not None and len(trades)>0:
                            for key, value in trades.items():
                                if value is not None:
                                    resp[key] = value

                self._update_order_from_exchange(order, resp)

                if order.get_active_order() is not None:
                    self.log(self.LOG_INFO, "Order {} trade order updated for {} -{}-> {} filled {}/{}".format(
                        order.id, order.start_currency, order.side, order.dest_currency, order.get_active_order().filled,
                        order.get_active_order().amount))
                else:
                    o = order.orders_history[-1]
                    self.log(self.LOG_INFO, "Order {} trade order closed with status {} filled {}/{}".format(
                        order.id, o.status, o.filled,
                        o.amount))

            elif order.order_command == "cancel":
                self.log(self.LOG_INFO, "Order {} cancelling trade order  {} -{}-> {} ".format(
                    order.id, order.start_currency, order.side, order.dest_currency))

                self.cancel_order(order.get_active_order())

                resp = self._update_order(order.get_active_order())
                order.active_order.update_order_from_exchange_resp(resp)  # workaround

                if resp["status"] == "closed" or resp["status"] == "canceled":
                    if resp["filled"] > 0:
                        trades = self._get_trade_results(order.get_active_order())
                        for key, value in trades.items():
                            if value is not None:
                                resp[key] = value

                resp["status"] = "canceled"  # override exchange responce

                self.log(self.LOG_INFO, "Order {} Fetching ticker {}".format(order.id, order.symbol))
                ticker = self.exchange._ccxt.fetch_ticker(order.symbol)
                price = core.get_symbol_order_price_from_tickers(order.start_currency, order.dest_currency,
                                                                 {order.symbol: ticker})["price"]

                self.log(self.LOG_INFO, "Order {} New price: {} (was {})".format(order.id, price, order.get_active_order().price))
                self._update_order_from_exchange(order, resp, {"price": price})

            else:
                raise OwaManagerError("Unknown order command")

            if order.status != "open":

                self.log(self.LOG_INFO, "Order {} Status: {}. State {}. Total filled {}/{}".format(order.id,
                    order.status, order.state, order.filled, order.amount))

                self._last_update_closed_orders.append(order)
                # self.on_order_close(order)

    def get_closed_orders(self):
        """
        get the list of orders which became closed from the lasyt update
        :return: list of closed orders or None if there is no any
        """
        if len(self._last_update_closed_orders) >0:
            return self._last_update_closed_orders
        else:
            return None
