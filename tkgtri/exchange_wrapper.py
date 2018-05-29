import ccxt
import csv
import json
from . import exchanges


class ExchangeWrapperError(Exception):
    """Basic exception for errors raised by cars"""
    pass


class ExchangeWrapperOfflineFetchError(ExchangeWrapperError):
    """Basic exception for errors raised by cars"""
    pass


class ccxtExchangeWrapper:
    _ccxt = ...  # type: ccxt.base

    @classmethod
    def load_from_id(cls, exchange_id, api_key="", secret="", offline=False):

        try:
            exchange = getattr(exchanges, exchange_id)
            exchange = exchange(exchange_id, api_key, secret)
            return exchange
        except AttributeError:
            return cls(exchange_id, api_key, secret, offline)

    def __init__(self, exchange_id, api_key="", secret="", offline=False):

        exchange = getattr(ccxt, exchange_id)

        self._ccxt = exchange({'apiKey': api_key, 'secret': secret})
        self.wrapper_id = "generic"
        self.offline = offline

        self._offline_markets = dict()
        self._offline_tickers = dict()
        self._offline_tickers_current_index = int

        self.markets_json_file = str
        self.tickers_csv_file = str

    def get_markets(self):
        return self._ccxt.load_markets()

    def get_tickers(self):
        return self._ccxt.fetch_tickers()

    def get_exchange_wrapper_id(self):
        return "generic"

    # offline fetching
    def set_offline_mode(self, markets_json_file: str, tickers_csv_file: str):

        self.markets_json_file = markets_json_file
        self.tickers_csv_file = tickers_csv_file

        self.offline = True
        self._offline_tickers_current_index = 0

        self._offline_markets = self.load_markets_from_json_file(markets_json_file)
        self._offline_tickers = self.load_tickers_from_csv(tickers_csv_file)

    @staticmethod
    def load_markets_from_json_file(markets_json_file):

        with open(markets_json_file) as json_file:
            json_data = json.load(json_file)

        return json_data

    @staticmethod
    def load_tickers_from_csv(tickers_csv_file):
        tickers = dict()

        with open(tickers_csv_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if int(row["fetch_id"]) not in tickers:
                    tickers[int(row["fetch_id"])] = dict()

                tickers[int(row["fetch_id"])][row["symbol"]] = dict({"ask": float(row["ask"]),
                                                                     "bid": float(row["bid"]),
                                                                     "askVolume": float(row["askVolume"]),
                                                                     "bidVolume": float(row["bidVolume"])})
        return tickers

    def _offline_fetch_tickers(self):
        if self._offline_tickers_current_index < len(self._offline_tickers):
            tickers = self._offline_tickers[self._offline_tickers_current_index]
            self._offline_tickers_current_index += 1

        else:
            raise(ExchangeWrapperOfflineFetchError(
                "No more loaded tickers. Total tickers: {}".format(len(self._offline_tickers))))
        return tickers

