import ccxt
import ccxt.async_support as accxt
import asyncio
import csv
import json
import uuid
import time
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
    def load_from_id(cls, exchange_id, api_key=None, secret=None, offline=False):

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
        self._offline_order_cancelled = False

        self._offline_trades = list()

        # _offline_orders_data - dict of off-line orders data as {order_id: {
        #                                                               "_offline_order": {}
        #                                                               "_offline_order_update_index": int
        #                                                               "_offline_order_cancelled": {}
        #                                                               "_offline_order_trades" : {}
        self._offline_orders_data = dict()
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
            self.tickers = self._fetch_tickers()
            return self.tickers
        else:
            self.tickers = self._offline_fetch_tickers()
            return self.tickers

    def get_exchange_wrapper_id(self):
        return "generic"

    # init offline fetching
    def set_offline_mode(self, markets_json_file: str, tickers_csv_file: str, orders_json_file: str = None):

        self.markets_json_file = markets_json_file
        self.tickers_csv_file = tickers_csv_file

        self.offline = True
        self._offline_tickers_current_index = 0
        if markets_json_file is not None:
            self._offline_markets = self.load_markets_from_json_file(markets_json_file)
        if tickers_csv_file is not None:
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

    def _offline_create_order(self, order: TradeOrder=None):
        if order is not None and order.internal_id in self._offline_orders_data:
            return self._offline_orders_data[order.internal_id]["_offline_order"]["create"]
        return self._offline_order["create"]

    def _offline_fetch_order(self, order: TradeOrder=None):

        if order is not None and order.internal_id in self._offline_orders_data:
            _offline_order_update_index = self._offline_orders_data[order.internal_id]["_offline_order_update_index"]
            _offline_order = self._offline_orders_data[order.internal_id]["_offline_order"]
            _offline_order_cancelled = self._offline_orders_data[order.internal_id]["_offline_order_cancelled"]

        else:
            _offline_order_update_index = self._offline_order_update_index
            _offline_order = self._offline_order
            _offline_order_cancelled = self._offline_order_cancelled

        if _offline_order_update_index < len(_offline_order["updates"]):
            order_resp = _offline_order["updates"][_offline_order_update_index]

            if not _offline_order_cancelled:
                if order is not None and order.internal_id in self._offline_orders_data:
                    self._offline_orders_data[order.internal_id]["_offline_order_update_index"] += 1
                else:
                    self._offline_order_update_index += 1
            else:
                order_resp = _offline_order["cancel"]

            return order_resp

        else:
            raise(ExchangeWrapperOfflineFetchError(
                "No more order updates in file. Total tickers: {}".format(len(self._offline_order["updates"]))))

    def _offline_cancel_order(self, order: TradeOrder=None):

        if order is not None and order.internal_id in self._offline_orders_data:

            if "cancel" not in self._offline_orders_data[order.internal_id]["_offline_order"]:
                # self._offline_order["cancel"] = True
                self._offline_orders_data[order.internal_id]["_offline_order"]["cancel"] = dict({"status": "canceled"})

            if not self._offline_orders_data[order.internal_id]["_offline_order_cancelled"]:
                self._offline_orders_data[order.internal_id]["_offline_order_update_index"] -= 1

            self._offline_orders_data[order.internal_id]["_offline_order_cancelled"] = True
            return self._offline_orders_data[order.internal_id]["_offline_order"]["cancel"]

        else:
            if "cancel" not in self._offline_order:
                # self._offline_order["cancel"] = True
                self._offline_order["cancel"] = dict({"status": "canceled"})

            if not self._offline_order_cancelled:
                self._offline_order_update_index -= 1

            self._offline_order_cancelled = True
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
            return self._offline_create_order(order)
        else:
            return self._create_order(order.symbol, "limit", order.side, order.amount, order.price)

    def get_order_update(self, order: TradeOrder):
        if self.offline:
            return self._offline_fetch_order(order)
        else:
            return self._fetch_order(order)

    def cancel_order(self, order: TradeOrder):
        if self.offline:
            return self._offline_cancel_order(order)
        else:
            return self._cancel_order(order)

    def offline_load_trades_from_file(self, trades_json_file):
        with open(trades_json_file) as json_file:
            json_data = json.load(json_file)
        self._offline_trades = json_data["trades"]

    def _offline_fetch_trades(self):

        if self._offline_order["updates"][self._offline_order_update_index-1]["trades"] is not None and \
                len(self._offline_order["updates"][self._offline_order_update_index-1]["trades"]) > 0:
            return self._offline_order["updates"][self._offline_order_update_index-1]["trades"]

        if self._offline_trades is not None :
            return self._offline_trades

        else:
            raise ExchangeWrapperOfflineFetchError(
                "Offline trades are not loaded")

    def _fetch_order_trades(self, order):
        pass

    def get_trades(self, order: TradeOrder):
        """
        get trades and checks if amount in trades equal to order's filled amount
        :param order:
        :return: dict of trades as in ccxt:
            amount:
            trades: list of trades
        """
        if self.offline:
            return order.trades
        else:
            amount_from_trades = 0

            if len(order.trades) > 0:
                amount_from_trades = self.amount_to_precision(order.symbol,
                                                              sum(item['amount'] for item in order.trades))

            if order.filled != amount_from_trades:
                resp = self._fetch_order_trades(order)
                amount_from_trades = self.amount_to_precision(order.symbol, sum(item['amount'] for item in resp))
            else:
                resp = order.trades

            if len(resp) > 0 and\
                    (order.filled == amount_from_trades or
                     abs(order.filled - amount_from_trades) <=
                     1/(10*(self.markets[order.symbol]["precision"]["amount"]-1))):
                return resp

            else:
                raise ExchangeWrapperError("Amount in Trades is not matching order filled Amount {} != {}".format(
                    amount_from_trades, order.filled))

    @staticmethod
    def fees_from_order(order:TradeOrder):
        """
        returns the dict of cumulative fee as ["<CURRENCY>"]["amount"]

        :param trades: list of ccxt trades
        :return:  the dict of cumulative fee as ["<CURRENCY>"]["amount"]
        """
        #trades = trades
        total_fee = dict()

        for t in order.trades:
            if "fee" not in t:
                break

            if t["fee"]["currency"] not in total_fee:
                total_fee[t["fee"]["currency"]] = dict()
                total_fee[t["fee"]["currency"]]["amount"] = 0

            total_fee[t["fee"]["currency"]]["amount"] += t["fee"]["cost"]

        for c in order.start_currency, order.dest_currency:
            if c not in total_fee:
                total_fee[c] = dict({"amount": 0.0})

        return total_fee
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
        results["filled"] =  results["amount"]
        results["cost"] = self.price_to_precision(order.symbol, results["cost"])

        results["price"] = self.price_to_precision(order.symbol, results["cost"] / results["amount"])

        if order.side == "buy":
            results["dest_amount"] = results["filled"]
            results["src_amount"] = results["cost"]

        elif order.side == "sell":
            results["dest_amount"] = results["cost"]
            results["src_amount"] = results["filled"]

        results["amount"] = None
        return results

    def amount_to_precision(self, symbol, amount):
        if self._ccxt is not None and not self.offline:
            return float(self._ccxt.amount_to_precision(symbol, amount))

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
        if not self.offline:
            ob = await self._async_ccxt.fetch_order_book(symbol, 100)
        else:
            ob = self._create_order_book_array_from_ticker(self.tickers[symbol])
        ob["symbol"] = symbol
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

    def get_order_books_async(self, symbols):
        loop = asyncio.get_event_loop()
        tasks = list()

        for s in symbols:
            tasks.append(self._get_order_book_async(s))

        ob_array = loop.run_until_complete(asyncio.gather(*tasks))
        return ob_array

    def fetch_free_balance(self):
        return self._ccxt.fetch_free_balance()

    def _create_order_book_array_from_ticker(self, ticker):
        ob = dict()
        ob["asks"] = [[ticker["ask"], 99999999]]
        ob["bids"] = [[ticker["bid"], 99999999]]
        return ob

    def create_order_offline_data(self, order: TradeOrder, updates_to_fill: int = 1):
        order_resp = dict()
        order_resp["create"] = dict()
        order_resp["create"]["amount"] = self.amount_to_precision(order.symbol, order.amount)
        order_resp["create"]["price"] = self.price_to_precision(order.symbol, order.price)
        order_resp["create"]["status"] = "open"
        order_resp["create"]["filled"] = 0.0
        order_resp["create"]["id"] = str(uuid.uuid4())
        order_resp["create"]["timestamp"] = int(time.time()*1000)

        order_resp["updates"] = list()
        order_resp["trades"] = list()

        for i in range(0, updates_to_fill):
            update = dict()
            update["filled"] = order.amount * ((i+1)/updates_to_fill)
            update["cost"] = update["filled"] * order.price
            update["status"] = "open"

            trade = dict({"amount":  order.amount / updates_to_fill,
                          "price":  order.price,
                          "cost":  (order.amount / updates_to_fill)*order.price,
                          "order": order_resp["create"]["id"]})

            if i > 0:
                update["trades"] = order_resp["updates"][i-1]["trades"][0:i]
            else:
                update["trades"] = list()

            update["trades"].append(trade)

            if i == updates_to_fill-1:
                update["status"] = "closed"
                update["filled"] = order.amount
                update["cost"] = update["filled"] * order.price

            order_resp["updates"].append(update)

       #order_resp["trades"] = update["trades"]

        order_resp["cancel"] = dict({"status": "canceled"})

        return order_resp

    def add_offline_order_data(self, order:TradeOrder, updates_to_fill=1):
        o = self.create_order_offline_data(order, updates_to_fill)
        order_id = order.internal_id
        self._offline_orders_data[order_id] = dict()
        self._offline_orders_data[order_id]["_offline_order"] = o
        self._offline_orders_data[order_id]["_offline_trades"] = o['trades']
        self._offline_orders_data[order_id]["_offline_order_update_index"] = 0
        self._offline_orders_data[order_id]["_offline_order_cancelled"] = False
        return order_id






