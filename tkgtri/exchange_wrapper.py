import ccxt
from . import exchanges


class ccxtExchangeWrapper:

    @classmethod
    def load_from_id(cls, exchange_id, api_key ="", secret =""):

        try:
            exchange = getattr(exchanges, exchange_id)
            exchange = exchange(exchange_id, api_key, secret)
            return exchange
        except AttributeError:
            return cls(exchange_id, api_key, secret)

    def __init__(self, exchange_id, api_key="", secret=""):

        exchange = getattr(ccxt, exchange_id)

        self._ccxt = exchange({'apiKey': api_key, 'secret': secret})
        self.wrapper_id = "generic"

    def get_markets(self):
        return self._ccxt.load_markets()

    def get_tickers(self):
        return self._ccxt.fetch_tickers()

    def get_exchange_wrapper_id(self):
        return "generic"
