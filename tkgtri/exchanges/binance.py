from .. import exchange_wrapper as ew


class binance(ew.ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(binance, self).__init__(exchange_id, api_key ="", secret ="")
        self.wrapper_id = "binance"

    def _fetch_tickers(self):
        return self._ccxt.fetch_bids_asks()

    def get_exchange_wrapper_id(self):
        return self.wrapper_id

