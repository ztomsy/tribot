from .trade_orders import *
from .exchange_wrapper import ccxtExchangeWrapper

class exchangeOrder(object):

    # mapping from  ccxt order to TradeOder fields {"ccxt_order_field":"TKG Order field"}
    #

    ex_order_mapping_update_fields = dict({"id": "id", "status": "status", "symbol": "symbol", "type": "type",
                                           "side": "side", "amount": "amount", "timestamp": "timestamp"})

    def __init__(self, exchange_wrapper: ccxtExchangeWrapper):

        self.exchange_wrapper = exchange_wrapper
        self.order = None
        self.ccxt_order = None

    def create_limit_order_from_start_amount(self, start_currency, amount_start, dest_currency, price):

        self.order = TradeOrder.create_limit_order_from_start_amount(self.exchange_wrapper.markets, start_currency,
                                                                     amount_start, dest_currency, price)

        resp_order = self.exchange_wrapper.create_limit_order()
        self.ccxt_order = resp_order  # saving order info for future

        self.order.update_from_exchange(resp_order)


    def update_order_from_exchange(self, order_resp: dict, order: TradeOrder = None):

        if order is None:
            order_to_update = self.order
        else:
            order_to_update = order

        for ex_field, order_field in self.ex_order_mapping_update_fields.items():
            setattr(order_to_update, order_field, order_resp[ex_field])
