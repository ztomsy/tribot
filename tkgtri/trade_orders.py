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
    UPDATE_FROM_EXCHANGE_FIELDS = ["id", "datetime", "timestamp", "lastTradeTimestamp", "status", "amount", "filled",
                                   "remaining", "cost", "info"]

    def __init__(self, type, symbol, amount, side):

        self.id = str
        self.datetime = datetime  # datetime
        self.timestamp = int  # order placing/opening Unix timestamp in milliseconds
        self.lastTradeTimestamp = int  # Unix timestamp of the most recent trade on this order
        self.status = str  # 'open', 'closed', 'canceled'

        self.symbol = symbol.upper()
        self.type = str  # limit
        self.side = side.lower()  # buy or sell
        self.amount = amount  # ordered amount of base currency
        self.filled = 0.0  # filled amount of base currency
        self.remaining = 0.0  # remaining amount to fill
        self.cost = 0.0  # 'filled' * 'price'

        self.info = None  # the original response from exchange

        self.order_book = None
        self.result = OrderResult

        self.amount_start = float  # amount of start currency

    @classmethod
    def create_limit_order_from_start_amount(cls, symbol, start_currency, amount_start, dest_currency, price):

        side = core.get_order_type(start_currency, dest_currency, symbol)

        if not side:
            raise OrderErrorSymbolNotFound("Worng symbol {} for trade {} - {}".format(symbol, start_currency, dest_currency))

        if price <= 0:
            raise (OrderErrorBadPrice("Wrong price. Symbol: {}, Side:{}, Price:{} ".format(symbol, side, price)))

        if side == "sell":
            amount = amount_start
        elif side == "buy":
            amount = amount_start / price

        order = cls("limit", symbol, amount, side)
        order.amount_start = amount_start
        return order

    def cancel_order(self):
        pass

    def update_order_from_exchange_resp(self, exchange_data: dict):

        for field in self.UPDATE_FROM_EXCHANGE_FIELDS:
            if exchange_data[field] is not None:
                setattr(self, field, exchange_data[field])

        pass

    def get_filled_amount_in_dest(self):
        pass

    def get_filled_amount_in_source(self):
        pass

    def recover_start_currency(self):
        pass

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
