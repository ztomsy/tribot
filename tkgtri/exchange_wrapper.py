import ccxt
import csv
import json
from . import exchanges


class ExchangeWrapperError(Exception):
    """Basic exception for errors raised by ccxtExchangeWrapper"""
    pass

class ExchangeWrapperOfflineFetchError(ExchangeWrapperError):
    """Exception for Offline fetching errors"""
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

        self.tickers = dict()
        self.markets = dict()

        self._offline_markets = dict()
        self._offline_tickers = dict()
        self._offline_tickers_current_index = 0

        self.markets_json_file = str
        self.tickers_csv_file = str

    # generic method for loading markets could be redefined in custom exchange wrapper
    def _load_markets(self):
        return self._ccxt.load_markets()

    # generic method for fetching tickers could be redefined in custom exchange wrapper
    def _fetch_tickers(self):
        return self._ccxt.fetch_tickers()

    def get_markets(self):
        if not self.offline:
            self.markets = self._load_markets()
            return self.markets

        else:
            self.markets = self._offline_load_markets()
            return self.markets

    def get_tickers(self):
        if not self.offline:
            return self._fetch_tickers()
        else:
            return self._offline_fetch_tickers()

    def get_exchange_wrapper_id(self):
        return "generic"

    # init offline fetching
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

        csv_float_fields = ["ask","bid","askVolume", "bidVolume"]

        with open(tickers_csv_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if int(row["fetch_id"]) not in tickers:
                    tickers[int(row["fetch_id"])] = dict()

                row_value = dict()
                for v in csv_float_fields:
                    try:
                        row_value[v] = float(row[v])
                    except ValueError:
                        row_value[v] = 0

                tickers[int(row["fetch_id"])][row["symbol"]] = dict({"ask": float(row_value["ask"]),
                                                                     "bid": float(row_value["bid"]),
                                                                     "askVolume": float(row_value["askVolume"]),
                                                                     "bidVolume": float(row_value["bidVolume"])})
        return tickers

    def _offline_fetch_tickers(self):
        if self._offline_tickers_current_index < len(self._offline_tickers):
            tickers = self._offline_tickers[self._offline_tickers_current_index]
            self._offline_tickers_current_index += 1
            return tickers

        else:
            raise(ExchangeWrapperOfflineFetchError(
                "No more loaded tickers. Total tickers: {}".format(len(self._offline_tickers))))

    def _offline_load_markets(self):
        if self._offline_markets is not None and len(self._offline_markets):
            return self._offline_markets

        else:
            raise (ExchangeWrapperOfflineFetchError(
                "Markets are not loaded".format(len(self._offline_tickers))))
