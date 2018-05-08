from tkgtri.exchange_wrapper import ccxtExchangeWrapper


class binance(ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(binance, self).__init__(exchange_id, api_key ="", secret ="")
        self.wrapper_id = "binance"

    def get_tickers(self):
        return self._ccxt.fetch_bid_asks()

    def get_exchange_wrapper_id(self):
        return self.wrapper_id

