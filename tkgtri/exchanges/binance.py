from tkgtri.exchange_wrapper import ccxtExchangeWrapper


class binance(ccxtExchangeWrapper):

    def get_tickers(self):
        return self._ccxt.fetch_bid_asks()