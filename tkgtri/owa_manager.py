from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
from tkgtri import OrderWithAim
from datetime import datetime
from tkgtri import errors
from tkgtri.errors import *

class OwaManager(object):

    def __init__(self, exchange: ccxtExchangeWrapper, max_order_update_attempts = 10, max_cancel_attempts=10):
        self.orders = list()

        self.max_order_update_attempts = max_order_update_attempts
        self.max_cancel_attempts = max_cancel_attempts

        self.last_update_time = datetime(1, 1, 1, 1, 1, 1, 1)

        self.orders = list()

        self.exchange = exchange

        self.LOG_DEBUG = "DEBUG"
        self.LOG_INFO = "INFO"
        self.LOG_ERROR = "ERROR"
        self.LOG_CRITICAL = "CRITICAL"


    def _create_order(self, order:TradeOrder):
        return self.exchange.place_limit_order(order)

    def _update_order(self, order: TradeOrder):
        return self.exchange.get_order_update(order)

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

        results = list()
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

    def _update_order_from_exchange(self, order: OrderWithAim, resp):

        try:
            order.update_from_exchange(resp)
        except Exception as e:
            self.log(self.LOG_ERROR, type(e).__name__)
            self.log(self.LOG_ERROR, e.args)

    def proceed_orders(self):

        open_orders = list(filter(lambda x: x.status != "closed" and x.active_order is not None, self.orders))

        for order in open_orders:

            if order.order_command == "new":
                if order.get_active_order().status != "open":
                    resp = self._create_order(order.get_active_order())
                    self._update_order_from_exchange(order, resp)

                else:
                    raise OwaManagerError("Order already set")

            elif order.order_command == "hold":
                resp = self._update_order(order.get_active_order())

                if resp["status"] == "closed" or resp["status"] == "canceled":
                    trades = self._get_trade_results(order.get_active_order())

                    for key, value in trades.items():
                        if value is not None:
                            resp[key] = value

                self._update_order_from_exchange(order, resp)

            elif order.order_command == "cancel":
                resp = self.cancel_order(order.get_active_order())

                if resp["status"] == "closed" or resp["status"] == "canceled":
                    for key, value in trades.items():
                        if value is not None:
                            resp[key] = value

                self._update_order_from_exchange(order, resp)

            else:
                raise OwaManagerError("Unknown order command")