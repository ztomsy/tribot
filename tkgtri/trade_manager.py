from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
from datetime import datetime


class OrderManagerError(Exception):
    pass


class OrderManagerErrorUnFilled(Exception):
    pass


class OrderManagerErrorSkip(Exception):
    pass


class OrderManagerCancelAttemptsExceeded(Exception):
    pass


class OrderManagerFok(object):

    # limits - dict of limits to wait till cancel the order. ex: {"BTC": 0.002, "ETH": 0.02, "BNB": 1, "USDT": 20}
    # updates_to_kill - number of updates after which to cancel the order if it's not filled
    # usage:
    # after init and the update of the order call the proceed_update
    # it should return:
    # - "complete_order" if the order was fully filled within the requests limit
    # - "cancel" to cancel the order because max amount of updates was reached and filled more that min amount so it's
    #    possible to recover
    # - "skip" - when the order have not reached the min amount within the number of updates limit. in case of tri arb
    #   it means razmotalo. just drop the triangle without recovery

    def __init__(self, order: TradeOrder, limits=None, updates_to_kill=100, max_cancel_attempts=10):
        self.order = order

        self.min_filled_dest_amount = float
        self.min_filled_src_amount = float

        self.order_update_requests = 0
        self.updates_to_kill = updates_to_kill
        self.max_cancel_attempts = max_cancel_attempts

        self.next_actions_list = ["hold," "cancel", "create_new"]
        self.next_action = str

        self.limits = dict

        self.min_filled_amount = float  # min amount of filled quote currency. should check cost in order to maintain

        if limits is not None:
            self.set_filled_min_amount(limits)

        self.last_response = dict()

        self.last_update_time = datetime(1, 1, 1, 1, 1, 1, 1)

    def set_filled_min_amount(self, limits: dict):
        self.limits = limits
        if self.order.symbol.split("/")[1] in limits:
            self.min_filled_amount = limits[self.order.symbol.split("/")[1]]
        else:
            raise OrderManagerError("Limit for {} not found".format(self.order.symbol))

    def on_order_create(self):
        print("Order {} created. Filled dest curr:{} / {} ".format(self.order.id, self.order.filled_dest_amount,
                                                                   self.order.amount_dest))
        return True

    def on_order_update(self):
        print("Order {} updated. Filled dest curr:{} / {} ".format(self.order.id, self.order.filled_dest_amount,
                                                                   self.order.amount_dest))

        return True

    def on_order_update_error(self, exception):
        print("Error on order_id: {}".format(self.order.id))
        print("Exception: {}".format(type(exception).__name__))
        print("Exception body:", exception.args)
        return True

    def proceed_update(self):
        response = dict()

        # if self.order.update_requests_count >= self.updates_to_kill > 0 and\
        #         (self.order.cost > self.min_filled_amount) and (self.order.status != "closed" or
        #                                                           self.order.status != "canceled"):
        #     response["action"] = "cancel"
        #     response["reason"] = "max number of updates and min amount reached"
        #     self.last_response = response
        #     return response

        if (self.order_update_requests +1 >= self.updates_to_kill) and\
                (self.order.status != "closed" or self.order.status != "canceled"):
            response["action"] = "cancel"
            response["reason"] = "max number of updates reached"
            response["status"] = self.order.status
            self.last_response = response
            return response

        elif self.order.status == "closed" or self.order.status == "canceled":
            response["action"] = "complete_order"
            response["reason"] = "order closed"
            response["status"] = self.order.status
            self.last_response = response
            return response

        response["action"] = "hold"
        response["reason"] = "max number of updates/limits not reached"
        self.last_response = response
        return response

    def _create_order(self, exchange_wrapper: ccxtExchangeWrapper):
        return exchange_wrapper.place_limit_order(self.order)

    def _update_order(self, exchange_wrapper: ccxtExchangeWrapper):
        return exchange_wrapper.get_order_update(self.order)

    def _cancel_order(self, exchange_wrapper: ccxtExchangeWrapper):
        exchange_wrapper.cancel_order(self.order)


    # blocking method !!!!!
    def cancel_order(self, exchange):
        cancel_attempt = 0

        while self.order.status != "canceled" and self.order.status != "closed":
            cancel_attempt += 1
            try:
                self._cancel_order(exchange)

            except Exception as e:
                self.on_order_update_error(e)

            finally:

                try:
                    resp = self._update_order(exchange)
                    self.order.update_order_from_exchange_resp(resp)
                except Exception as e1:
                    self.on_order_update_error(e1)

                if cancel_attempt >= self.max_cancel_attempts:
                    raise OrderManagerCancelAttemptsExceeded("Cancel Attempts Exceeded")

        return True

    # blocking method !!!!!
    def fill_order(self, exchange):

        order_resp = self._create_order(exchange)
        self.order.update_order_from_exchange_resp(order_resp)
        self.on_order_create()

        while  self.proceed_update()["action"] == "hold":
            self.order_update_requests += 1
            try:
                update_resp = self._update_order(exchange)
                self.order.update_order_from_exchange_resp(update_resp)
                self.on_order_update()

            except Exception as e:
                self.on_order_update_error(e)

        if self.last_response["action"] == "complete_order":
            return True

        if self.last_response["action"] == "cancel":
            raise OrderManagerErrorUnFilled("Order not filled: {}".format(self.last_response["reason"]))

        raise OrderManagerError("Order not filled: Unknown error")
