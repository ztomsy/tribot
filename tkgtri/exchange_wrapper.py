import ccxt
import ccxt.async_support as accxt
import asyncio
import csv
import json
from . import exchanges
from . import core
from .trade_orders import TradeOrder

class ExchangeWrapperError(Exception):
    """Basic exception for errors raised by ccxtExchangeWrapper"""
    pass

class ExchangeWrapperOfflineFetchError(ExchangeWrapperError):
    """Exception for Offline fetching errors"""
    pass


class ccxtExchangeWrapper:

    _ccxt = ...  # type: ccxt.Exchange
    _async_ccxt = ...  # type accxt.Exchange
    _PRECISION_AMOUNT = 8  # default amount precision for offline mode
    _PRECISION_PRICE = 8  # default price precision for offline mode

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

        self.exchange_id = exchange_id

        self._ccxt = exchange({'apiKey': api_key, 'secret': secret})
        self.wrapper_id = "generic"
        self.offline = offline

        self.tickers = dict()
        self.markets = dict()

        self._offline_markets = dict()
        self._offline_tickers = dict()
        self._offline_tickers_current_index = 0

        self._offline_order = dict()
        self._offline_order_update_index = 0

        self._offline_trades = list()

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
    def set_offline_mode(self, markets_json_file: str, tickers_csv_file: str, orders_json_file: str = None):

        self.markets_json_file = markets_json_file
        self.tickers_csv_file = tickers_csv_file

        self.offline = True
        self._offline_tickers_current_index = 0

        self._offline_markets = self.load_markets_from_json_file(markets_json_file)
        self._offline_tickers = self.load_tickers_from_csv(tickers_csv_file)

        if orders_json_file is not None:
            self._offline_order = self.load_order_from_json(orders_json_file)

    @staticmethod
    def load_markets_from_json_file(markets_json_file):

        with open(markets_json_file) as json_file:
            json_data = json.load(json_file)

        return json_data

    @staticmethod
    def load_tickers_from_csv(tickers_csv_file):
        tickers = dict()

        csv_float_fields = ["ask", "bid", "askVolume", "bidVolume"]

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
                        row_value[v] = None

                tickers[int(row["fetch_id"])][row["symbol"]] = dict({"ask": row_value["ask"],
                                                                     "bid": row_value["bid"],
                                                                     "askVolume": row_value["askVolume"],
                                                                     "bidVolume": row_value["bidVolume"]})
        return tickers

    @staticmethod
    def load_order_from_json(order_jason_file):
        with open(order_jason_file) as json_file:
            json_data = json.load(json_file)
        return json_data

    def _offline_fetch_tickers(self):
        if self._offline_tickers_current_index < len(self._offline_tickers):
            tickers = self._offline_tickers[self._offline_tickers_current_index]
            self._offline_tickers_current_index += 1
            return tickers

        else:
            raise(ExchangeWrapperOfflineFetchError(
                "No more loaded tickers. Total tickers: {}".format(len(self._offline_tickers))))

    def _offline_create_order(self):
        return self._offline_order["create"]

    def _offline_fetch_order(self):

        if self._offline_order_update_index < len(self._offline_order["updates"]):
            order_resp = self._offline_order["updates"][self._offline_order_update_index]
            self._offline_order_update_index += 1
            return order_resp

        else:
            raise(ExchangeWrapperOfflineFetchError(
                "No more order updates in file. Total tickers: {}".format(len(self._offline_order["updates"]))))

    def _offline_cancel_order(self):
        if "cancel" not in self._offline_order:
            self._offline_order["cancel"] = True
        return self._offline_order["cancel"]

    def _offline_load_markets(self):
        if self._offline_markets is not None and len(self._offline_markets):
            return self._offline_markets

        else:
            raise (ExchangeWrapperOfflineFetchError(
                "Markets are not loaded".format(len(self._offline_tickers))))

    def _create_order(self, symbol, order_type, side, amount, price=None):
        # create_order(self, symbol, type, side, amount, price=None, params={})
        return self._ccxt.create_order(symbol, order_type, side, amount, price)

    def _fetch_order(self, order: TradeOrder):
        return self._ccxt.fetch_order(order.id)

    def _cancel_order(self, order: TradeOrder):
        return self._ccxt.cancel_order(order.id)

    def place_limit_order(self, order: TradeOrder):
        # returns the ccxt response on order placement
        if self.offline:
            return self._offline_create_order()
        else:
            return self._create_order(order.symbol, "limit", order.side, order.amount, order.price)

    def get_order_update(self, order: TradeOrder):
        if self.offline:
            return self._offline_fetch_order()
        else:
            return self._fetch_order(order)

    def cancel_order(self, order: TradeOrder):
        if self.offline:
            return self._offline_cancel_order()
        else:
            return self._cancel_order(order)

    def offline_load_trades_from_file(self, trades_json_file):
        with open(trades_json_file) as json_file:
            json_data = json.load(json_file)
        self._offline_trades = json_data["trades"]

    def _offline_fetch_trades(self):
        if self._offline_trades is not None :
            return self._offline_trades

        else:
            raise ExchangeWrapperOfflineFetchError(
                "Offline trades are not loaded")

    def _fetch_order_trades(self, order):
        self._ccxt.fetch_order_trades(order.id)

    def get_trades(self, order):
        if self.offline:
            return self._offline_fetch_trades()
        else:
            return self._fetch_order_trades(order)
    #
    # fetch or (get from order) the trades within the order and return the result calculated by trades:
    # dict = {
    #       "trades": dict of trades from ccxt
    #       "amount" : filled amount of order (base currency)
    #       "cost": filled amount if quote currency
    #       "price" : total order price
    #       "dest_amount" : amount of received destination currency
    #       "src_amount" :  amount of spent source currency

    def get_trades_results(self, order: TradeOrder):

        trades = self.get_trades(order)
        results = order.total_amounts_from_trades(trades)
        results["trades"] = trades
        results["amount"] = self.amount_to_precision(order.symbol, results["amount"])
        results["cost"] = self.price_to_precision(order.symbol, results["cost"])

        results["price"] = self.price_to_precision(order.symbol, results["cost"] / results["amount"])

        if order.side == "buy":
            results["dest_amount"] = results["amount"]
            results["src_amount"] = results["cost"]

        elif order.side == "sell":
            results["dest_amount"] = results["cost"]
            results["src_amount"] = results["amount"]

        return results

    def amount_to_precision(self, symbol, amount):
        if self._ccxt is not None and not self.offline:
            return self._ccxt.amount_to_precision(symbol, amount)

        elif self.markets is not None and symbol in self.markets and self.markets[symbol] is not None \
                and "precision" in self.markets[symbol]:
            return core.amount_to_precision(amount, self.markets[symbol]["precision"]["amount"])

        else:
            return core.amount_to_precision(amount, self._PRECISION_AMOUNT)

    def price_to_precision(self, symbol, amount):
        if self._ccxt is not None and not self.offline:
            return float(self._ccxt.price_to_precision(symbol, amount))
        elif self.markets is not None and symbol in self.markets and self.markets[symbol] is not None \
                and "precision" in self.markets[symbol]:
            return core.price_to_precision(amount, self.markets[symbol]["precision"]["price"])
        else:
            return core.price_to_precision(amount, self._PRECISION_PRICE)

    @staticmethod
    async def _async_load_markets(exchange):
        await exchange.load_markets()

    async def _get_order_book_async(self, symbol):
        ob = await self._async_ccxt.fetch_order_book(symbol)
        return ob

    def init_async_exchange(self):
        """
        init async ccxt exchange object and load markets
        :return: none
        """
        exchange_async = getattr(accxt, self.exchange_id)
        self._async_ccxt = exchange_async()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_load_markets(self._async_ccxt))

    def get_oder_books_async(self, symbols):
        loop = asyncio.get_event_loop()
        tasks = list()

        for s in symbols:
            tasks.append(self._get_order_book_async(s))

        ob_array = loop.run_until_complete(asyncio.gather(*tasks))
        return ob_array

    def fetch_free_balance(self):
        return self._ccxt.fetch_free_balance()