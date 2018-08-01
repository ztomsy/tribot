from .orderbook import OrderBook
from tkgtri import core
from datetime import datetime


class OrderError(Exception):
    """Basic exception for errors raised by Orders"""
    pass


class OrderErrorSymbolNotFound(OrderError):
    """Basic exception for errors raised by cars"""
    pass


class OrderErrorBadPrice(OrderError):
    pass


class OrderErrorSideNotFound(OrderError):
    pass


class OrderResult:
    def __init__(self):
        self.id = ""

        self.amount = 0  # result amount if buy than base, if sell than quoote
        self.asset = ""  # result asset

        self.quote_amount = 0
        self.quote_asset = ""
        self.base_amount = 0

        self.response = ""

        self.commission = 0
        self.commission_asset = ""

        self.fills_depth = 0
        self.status = ""
        self.placed = False


class TradeOrder(object):
    # todo create wrapper constructor for fake/real orders with any starting asset
    # different wrapper constructors for amount of available asset
    # so developer have not to implement the bid calculation
    #
    # TradeOrder.fake_order_from_asset(symbol, start_asset, amount, ticker_price, order_book = None, exchange = None,
    #  commission = 0 )
    #
    # TradeOrder.order_from_asset(symbol, start_asset, amount, ticker_price, exchange )
    #

    # fields to update from ccxt order placement response
    _UPDATE_FROM_EXCHANGE_FIELDS = ["id", "datetime", "timestamp", "lastTradeTimestamp", "status", "amount", "filled",
                                   "remaining", "cost", "price", "info", "trades", "fee"]

    def __init__(self, type, symbol, amount, side, price=None, precision_amount=None, precision_price=None):

        self.id = str
        self.datetime = datetime  # datetime
        self.timestamp = int  # order placing/opening Unix timestamp in milliseconds
        self.lastTradeTimestamp = int  # Unix timestamp of the most recent trade on this order
        self.status = str  # 'open', 'closed', 'canceled'

        self.symbol = symbol.upper()
        self.type = type  # limit
        self.side = side.lower()  # buy or sell
        self.amount = amount  # ordered amount of base currency
        self.init_price = price if price is not None else 0.0 # initial price, when create order
        self.price = self.init_price  # placed price, could be updated from exchange

        self.precision_amount = precision_amount
        self.price_precision = precision_price


        self.filled = 0.0  # filled amount of base currency
        self.remaining = 0.0  # remaining amount to fill
        self.cost = 0.0  # filled amount of quote currency 'filled' * 'price'

        self.info = None  # the original response from exchange

        self.order_book = None
        self.result = OrderResult

        self.amount_start = float  # amount of start currency
        self.amount_dest = float # amount of dest currency

        self.update_requests_count = 0  # number of updates of order. should be in correspondence with API requests

        self.filled_src_amount = 0.0  # filled amount of start currency
        self.filled_dest_amount = 0.0  # filled amount of dest currency

        self.start_currency = self.symbol.split("/")[1] if side == "buy" else self.symbol.split("/")[0]
        self.dest_currency = self.symbol.split("/")[0] if side == "buy" else self.symbol.split("/")[1]

        # if not side:
        #     raise OrderErrorSymbolNotFound("Wrong symbol {} for trade {} - {}".format(symbol, start_currency,
        # dest_currency))

        if price is not None:
            if side == "sell":

                self.amount_start = amount
                self.amount_dest = self.amount_start * price

            elif side == "buy":
                self.amount_start = price * self.amount
                self.amount_dest = amount

    @classmethod
    def create_limit_order_from_start_amount(cls, symbol, start_currency, amount_start, dest_currency, price):

        side = core.get_order_type(start_currency, dest_currency, symbol)

        if not side:
            raise OrderErrorSymbolNotFound("Wrong symbol {} for trade {} - {}".format(symbol, start_currency, dest_currency))

        if price <= 0:
            raise (OrderErrorBadPrice("Wrong price. Symbol: {}, Side:{}, Price:{} ".format(symbol, side, price)))

        if side == "sell":
            amount = amount_start
            # amount_dest = amount_start * price

        elif side == "buy":
            amount = amount_start / price
            # amount_dest = amount

        order = cls("limit", symbol, amount, side, price)

        # order.amount_start = amount_start
        # order.amount_dest = amount_dest

        return order

    def cancel_order(self):
        pass

    def update_order_from_exchange_resp(self, exchange_data: dict):

        for field in self._UPDATE_FROM_EXCHANGE_FIELDS:
            if field in exchange_data and exchange_data[field] is not None:
                setattr(self, field, exchange_data[field])

        if self.side == "buy":
            self.filled_src_amount = self.cost
            self.filled_dest_amount = self.filled

        elif self.side == "sell":
            self.filled_src_amount = self.filled
            self.filled_dest_amount = self.cost

        self.update_requests_count += 1


    def get_filled_amount_in_dest(self):
        pass

    def get_filled_amount_in_source(self):
        pass

    def recover_start_currency(self):
        pass

    # will return the dict:
    # "amount" - total amount of base currency filled
    # "cost" - total amount of quote currency filled
    # "price" - total (average) price of fills = cost / amount
    def total_amounts_from_trades(self, trades):

        total = dict()
        total["amount"] = 0.0
        total["cost"] = 0.0
        total["price"] = 0.0
        # total["_cost_from_ccxt"] = 0.0

        for trade in trades:
            if trade["order"] == self.id:
                total["amount"] += trade["amount"]
                total["cost"] += trade["amount"] * trade["price"]
                # total["_cost_from_ccxt"] += trade["cost"]

        total["price"] = total["cost"] / total["amount"]

        return total

    def fake_market_order(self, orderbook=None, exchange=None):

        if orderbook is None and exchange is None:
            raise OrderError("Orderbook or exchange are needed to be provided")

        if orderbook is not None and exchange is not None:
            raise OrderError("Provide only orderbook or exchange")

        if orderbook is not None and isinstance(orderbook, OrderBook):
            self.order_book = orderbook
        elif isinstance(orderbook, OrderBook):
            raise OrderError("Wrong order book provided")

        if orderbook is None and exchange is not None:
            ob_array = exchange.fetch_order_book(self.symbol)
            order_book = OrderBook(self.symbol, ob_array["asks"], ob_array["bids"])
            self.order_book = order_book

        depth = self.order_book.get_depth(self.amount, self.side.lower(), "base")

        if depth is not None:
            self.result.placed = True
            self.result.id = "1"
            self.result.quote_amount = depth.total_quantity
            self.result.quote_asset = depth.currency
            self.result.totalPrice = depth.total_price
            self.result.fills_depth = depth.depth

            if self.side == "SELL":
                self.result.asset = self.symbol.split("/")[1]
                self.result.amount = depth.total_quantity

            if self.side == "BUY":
                self.result.asset = self.symbol.split("/")[0]
                self.result.amount = self.amount

            return self.result

    # def get_bid_from_start_currency(self, amount):
