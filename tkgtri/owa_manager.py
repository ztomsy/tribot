from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
from tkgtri import OrderWithAim
from datetime import datetime
from tkgtri import errors


class OwaManager(object):

    def __init__(self, max_order_update_attempts = 10, max_cancel_attempts=10):
        self.orders = list()

        self.max_order_update_attempts = max_order_update_attempts
        self.max_cancel_attempts = max_cancel_attempts

        self.last_update_time = datetime(1, 1, 1, 1, 1, 1, 1)

    def _create_order(self, exchange_wrapper: ccxtExchangeWrapper):
        return exchange_wrapper.place_limit_order(self.order)

    def _update_order(self, exchange_wrapper: ccxtExchangeWrapper):
        return exchange_wrapper.get_order_update(self.order)

    def _cancel_order(self, exchange_wrapper: ccxtExchangeWrapper):
        exchange_wrapper.cancel_order(self.order)

    # blocking method !!!!!
    def cancel_order(self, trade_order, exchange):
        cancel_attempt = 0

        while trade_order.status != "canceled" and trade_order.status != "closed":
            cancel_attempt += 1
            try:
                self._cancel_order(exchange)

            except Exception as e:
                self.on_order_update_error(e)

            finally:

                try:
                    resp = self._update_order(exchange)
                    trade_order.update_order_from_exchange_resp(resp)
                except Exception as e1:
                    self.on_order_update_error(e1)

                if cancel_attempt >= self.max_cancel_attempts:
                    raise errors.OwaManagerCancelAttemptsExceeded("Cancel Attempts Exceeded")

        return True




