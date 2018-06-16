# -*- coding: utf-8 -*-
from .context import tkgtri
from tkgtri.trade_orders import *
import ccxt
import unittest


class TradeOrderTestSuite(unittest.TestCase):

    def test_trade_order_create(self):

        trade_order = TradeOrder("limit", "ETH/BTC", 1, "buy")

        self.assertEqual(trade_order.side, "buy")
        self.assertEqual(trade_order.symbol, "ETH/BTC")
        self.assertEqual(trade_order.amount, 1)

    def test_create_limit_order_from_start_amount(self):

        markets = dict({"ETH/BTC": True})

        order = TradeOrder.create_limit_order_from_start_amount(markets, "ETH", 1, "BTC", 0.08)
        self.assertEqual(order.symbol, "ETH/BTC")
        self.assertEqual(order.side, "sell")
        self.assertEqual(order.amount, 1)
        self.assertEqual(order.amount_start, 1)
        self.assertEqual(type(order.id), type)

        order = TradeOrder.create_limit_order_from_start_amount(markets, "BTC", 1, "ETH", 0.08)
        self.assertEqual(order.symbol, "ETH/BTC")
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.amount, 1/0.08)
        self.assertEqual(order.amount_start, 1)

        with self.assertRaises(OrderErrorSymbolNotFound) as cm:
            TradeOrder.create_limit_order_from_start_amount(markets, "BTC", 1, "USD", 0.08)
        e = cm.exception
        self.assertEqual(type(e), OrderErrorSymbolNotFound)

        with self.assertRaises(OrderErrorBadPrice) as cm:
            TradeOrder.create_limit_order_from_start_amount(markets, "BTC", 1, "ETH", 0)
        e = cm.exception
        self.assertEqual(type(e), OrderErrorBadPrice)



    #
    # def test_fake_trade_placement_exception(self):
    #
    #     trade_order = tkgtri.TradeOrder("ETH/BTC", 1, "buy")
    #
    #     with self.assertRaises(tkgtri.OrderError) as cm:
    #         trade_order.fake_market_order()
    #     e = cm.exception
    #
    #     self.assertEqual(e.args, ("Orderbook or exchange are needed to be provided", ))
    #
    # def test_fake_trade_placement_exception_both_order_book_and_excnage(self):
    #
    #     ob = dict()
    #     ob["asks"] = [[1, 2],
    #                   [1.1, 2],
    #                   [1.1, 3]]
    #
    #     ob["bids"] = [[0.99, 1],
    #                   [0.98, 2],
    #                   [0.07, 3]]
    #
    #     orderbook = tkgtri.OrderBook("ETH/BTC", ob["asks"], ob["bids"])
    #
    #     trade_order = tkgtri.TradeOrder("ETH/BTC", 1, "buy")
    #
    #     with self.assertRaises(tkgtri.OrderError) as cm:
    #         trade_order.fake_market_order(orderbook, ccxt.binance())
    #     e = cm.exception
    #
    #     self.assertEqual(e.args, ("Provide only orderbook or exchange",))
    #
    # def test_fake_trade_from_orders_book(self):
    #
    #     ob = dict()
    #     ob["asks"] = [[1, 2],
    #                   [1.1, 2],
    #                   [1.1, 3]]
    #
    #     ob["bids"] = [[0.99, 1],
    #                   [0.98, 2],
    #                   [0.07, 3]]
    #
    #     orderbook = tkgtri.OrderBook("ETH/BTC", ob["asks"], ob["bids"])
    #
    #     trade_order = tkgtri.TradeOrder("ETH/BTC", 3, "buy")
    #     trade_order.fake_market_order(orderbook)
    #
    #     self.assertEqual(trade_order.result.quote_amount, 3.1)
    #     self.assertEqual(trade_order.result.amount, 3)
    #     self.assertEqual(trade_order.result.asset, "ETH")
    #
    #     trade_order = tkgtri.TradeOrder("ETH/BTC", 2, "sell")
    #     trade_order.fake_market_order(orderbook)
    #
    #     self.assertEqual(trade_order.result.quote_amount, 1.97)
    #     self.assertEqual(trade_order.result.amount, 1.97)
    #     self.assertEqual(trade_order.result.asset, "BTC")
    #
    # def test_fake_trade_from_exchange(self):
    #     exchange = ccxt.binance()
    #     symbol = "ETC/BTC"
    #     amount = 1
    #     side = "buy"
    #
    #     trade_order = tkgtri.TradeOrder(symbol, amount, side)
    #     trade_order.fake_market_order(exchange=exchange)
    #
    #     trade_order2 = tkgtri.TradeOrder(symbol, amount, side)
    #     trade_order2.fake_market_order(orderbook=trade_order.order_book)
    #
    #     self.assertEqual(trade_order.result.quote_amount, trade_order2.result.quote_amount)


if __name__ == '__main__':
    unittest.main()