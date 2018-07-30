from .. import exchange_wrapper as ew


class binance(ew.ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(binance, self).__init__(exchange_id, api_key, secret )
        self.wrapper_id = "binance"

    def _fetch_tickers(self):
        return self._ccxt.fetch_bids_asks()

    def _create_order(self, symbol, order_type, side, amount, price=None):
        # create_order(self, symbol, type, side, amount, price=None, params={})
        resp = self._ccxt.create_order(symbol, order_type, side, amount, price, {"newOrderRespType": "FULL"})
        resp["cost"] = resp["info"]["cummulativeQuoteQty"]
        return resp

    def _fetch_order(self, order):
            resp = self._ccxt.fetch_order(order.id, order.symbol)
            resp["cost"] = resp["info"]["cummulativeQuoteQty"]
            return resp

    def _cancel_order(self, order):
        resp = self._ccxt.cancel_order(order.id, order.symbol)

        return resp

    def _fetch_order_trades(self, order):
        return self._ccxt.fetch_my_trades(order.symbol, order.timestamp)

    def get_exchange_wrapper_id(self):
        return self.wrapper_id


