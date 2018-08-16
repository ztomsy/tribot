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

        self.assertEqual(trade_order.start_currency, "BTC")
        self.assertEqual(trade_order.dest_currency, "ETH")

        trade_order = TradeOrder("limit", "ETH/BTC", 1, "sell")

        self.assertEqual(trade_order.side, "sell")
        self.assertEqual(trade_order.symbol, "ETH/BTC")
        self.assertEqual(trade_order.amount, 1)

        self.assertEqual(trade_order.start_currency, "ETH")
        self.assertEqual(trade_order.dest_currency, "BTC")




    def test_create_limit_order_from_start_amount(self):

        symbol = "ETH/BTC"

        order = TradeOrder.create_limit_order_from_start_amount(symbol, "ETH", 1, "BTC", 0.08)
        self.assertEqual(order.side, "sell")
        self.assertEqual(order.amount, 1)
        self.assertEqual(order.amount_start, 1)
        self.assertEqual(order.id, "")

        order = TradeOrder.create_limit_order_from_start_amount(symbol, "BTC", 1, "ETH", 0.08)
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.amount, 1/0.08)
        self.assertEqual(order.amount_start, 1)

        with self.assertRaises(OrderErrorSymbolNotFound) as cm:
            TradeOrder.create_limit_order_from_start_amount(symbol, "BTC", 1, "USD", 0.08)
        e = cm.exception
        self.assertEqual(type(e), OrderErrorSymbolNotFound)

        with self.assertRaises(OrderErrorBadPrice) as cm:
            TradeOrder.create_limit_order_from_start_amount(symbol, "BTC", 1, "ETH", 0)
        e = cm.exception
        self.assertEqual(type(e), OrderErrorBadPrice)

    @unittest.skip
    def test_update_order_from_exchange_data(self):

        binance_responce = {'price': 0.07946, 'trades': None, 'side': 'sell', 'type': 'limit', 'cost': 0.003973,
                            'status': 'closed',
               'info': {'symbol': 'ETHBTC', 'orderId': 169675546, 'side': 'SELL', 'timeInForce': 'GTC',
                        'price': '0.07946000',
                        'status': 'FILLED', 'clientOrderId': 'SwstQ0eZ0ZJKr2y4uPQin2', 'executedQty': '0.05000000',
                        'origQty': '0.05000000', 'type': 'LIMIT', 'transactTime': 1529586827997}, 'filled': 0.05,
               'timestamp': 1529586827997, 'fee': None, 'symbol': 'ETH/BTC', 'id': '169675546',
               'datetime': '2018-06-21T13:13:48.997Z', 'lastTradeTimestamp': None, 'remaining': 0.0, 'amount': 0.05}

        symbol = "ETH/BTC"

        order = TradeOrder.create_limit_order_from_start_amount(symbol, "ETH", 1, "BTC", 0.08)

        order.update_order_from_exchange_resp(binance_responce)
        for field in order._UPDATE_FROM_EXCHANGE_FIELDS:
            if binance_responce[field] is not None:
                self.assertEqual(binance_responce[field], getattr(order, field))

    def test_offline_sell_order(self):

        ex = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        ex.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv",
                            "test_data/orders_binance.json")

        self.assertEqual(len(ex._offline_order["updates"]), 4)
        self.assertEqual(ex._offline_order["create"]["id"], "170254693")

        ex.get_markets()
        ex.get_tickers()

        order = tkgtri.TradeOrder.create_limit_order_from_start_amount("ETH/BTC", "ETH", 0.05 / 3, "BTC", 0.077212)

        order_resp = ex.place_limit_order(order)
        order.update_order_from_exchange_resp(order_resp)

        self.assertEqual(order.filled, 0)
        self.assertEqual(order.status, "open")

        order_resps = dict()
        order_resps["updates"] = list()

        tick = 0
        while order.status != "closed" and order.status != "canceled":
            update_resp = ex.get_order_update(order)
            order.update_order_from_exchange_resp(update_resp)
            order_resps["updates"].append(update_resp)
            tick += 1

        self.assertEqual(len(order_resps["updates"]), 4)
        self.assertEqual(order.status, "closed")
        self.assertEqual(order.filled, 0.016)

        self.assertEqual(order.filled_start_amount, order.filled)
        self.assertEqual(order.filled_dest_amount, order.cost)

        self.assertListEqual(order_resps["updates"], ex._offline_order["updates"])

    def test_offline_buy_order(self):

        ex = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        ex.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv",
                            "test_data/orders_kucoin_buy.json")

        ex.get_markets()
        ex.get_tickers()

        order = tkgtri.TradeOrder.create_limit_order_from_start_amount("ETH/BTC", "BTC", 0.05, "ETH",
                                                                       0.07381590480571001)

        order_resp = ex.place_limit_order(order)
        order.update_order_from_exchange_resp(order_resp)

        order_resps = dict()
        order_resps["updates"] = list()

        tick = 0
        while order.status != "closed" and order.status != "canceled":
            update_resp = ex.get_order_update(order)
            order.update_order_from_exchange_resp(update_resp)
            order_resps["updates"].append(update_resp)
            tick += 1

        # self.assertEqual(len(order_resps["updates"]), 4)
        self.assertEqual(order.status, "closed")
        self.assertEqual(order.filled, order.filled_dest_amount)

        self.assertEqual(order.filled_start_amount, order.cost)
        self.assertEqual(order.filled_dest_amount, order.filled)

        self.assertListEqual(order_resps["updates"], ex._offline_order["updates"])

    def test_offline_sell_multi(self):

        ex = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        ex.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv",
                            "test_data/orders_kucoin_multi.json")

        ex.get_markets()
        ex.get_tickers()

        order = tkgtri.TradeOrder.create_limit_order_from_start_amount("ETH/BTC", "ETH", 0.5, "BTC",
                                                                       0.06633157807472399)

        order_resp = ex.place_limit_order(order)
        order.update_order_from_exchange_resp(order_resp)

        order_resps = dict()
        order_resps["updates"] = list()

        tick = 0
        while order.status != "closed" and order.status != "canceled":
            update_resp = ex.get_order_update(order)
            order.update_order_from_exchange_resp(update_resp)
            order_resps["updates"].append(update_resp)

            self.assertEqual(order.filled_start_amount, order.filled)
            self.assertEqual(order.filled_dest_amount, order.cost)

            tick += 1

        # self.assertEqual(len(order_resps["updates"]), 4)
        self.assertEqual(order.status, "closed")

        self.assertEqual(order.filled_start_amount, order.filled)
        self.assertEqual(order.filled_dest_amount, order.cost)

        self.assertListEqual(order_resps["updates"], ex._offline_order["updates"])

        # trades = ex.get_trades(order)
        #
        # self.assertListEqual(trades, order.trades)





    def test_total_amounts_from_trades(self):

        order = tkgtri.TradeOrder.create_limit_order_from_start_amount("ETH/BTC", "ETH", 0.5, "BTC",
                                                                       0.06633157807472399)
        order.id = 1

        trades = [
            {"amount": 1 , "price": 1, "order": 1},
            {"amount": 2, "price": 2, "order": 1},
            {"amount": 3, "price": 4, "order": 1},
            {"amount": 1, "price": 0.123456789, "order": 1}
            ]

        total = order.total_amounts_from_trades(trades)

        self.assertEqual(total["amount"], 7)
        self.assertEqual(total["cost"], 17.123456789)
        self.assertEqual(total["price"], 17.123456789 / 7)





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