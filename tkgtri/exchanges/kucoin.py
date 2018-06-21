from .. import exchange_wrapper as ew


class kucoin(ew.ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(kucoin, self).__init__(exchange_id, api_key, secret )
        self.wrapper_id = "kucoin"

    def _fetch_order(self, order_id, symbol, order_type: str):
        return self._ccxt.fetch_order(order_id, symbol, {"type": order_type.upper()})

    def get_order_update(self, order):
        return self._fetch_order(order.id, order.symbol, order.side)

    def get_exchange_wrapper_id(self):
        return self.wrapper_id
