import ccxt


class ccxtExchangeWrapper:

    def __init__(self, exchange_id, api_key = "", secret = ""):

        exchange = getattr(ccxt, exchange_id)

        self._ccxt = exchange({'apiKey': api_key, 'secret': secret})

    def get_markets(self):
        return self._ccxt.load_markets()

    def get_tickers(self):
        return self._ccxt.fetch_tickers()
