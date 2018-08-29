# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest


class ExchageWrapperTestSuite(unittest.TestCase):

    def test_create_wrapped(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "binance")
        self.assertEqual(exchange._ccxt.id, "binance")

    def test_create_wrapped2(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "kucoin")
        self.assertEqual(exchange._ccxt.id, "kucoin")

    def test_create_generic(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("bitfinex")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "generic")
        self.assertEqual(exchange._ccxt.id, "bitfinex")

    @unittest.skip
    def test_online_fetch_ticker_wrapped(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        self.assertEqual(exchange.get_tickers()["ETH/BTC"]["last"], None)

    def test_fetch_ticker_generic(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        self.assertIsNot(exchange.get_tickers()["ETH/BTC"]["last"], None)

    def test_load_markets_from_file(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        markets = exchange.load_markets_from_json_file("test_data/markets_binance.json")

        self.assertEqual(markets["ETH/BTC"]["active"], True)

    def test_load_tickers_from_csv(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        tickers = exchange.load_tickers_from_csv("test_data/tickers_binance.csv")

        self.assertEqual(len(tickers), 3)
        self.assertEqual(tickers[2]["ETH/BTC"]["ask"], 0.082975)

    def test_init_offline_mode(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")

        self.assertEqual(exchange.offline, True)
        self.assertEqual(exchange._offline_tickers[2]["ETH/BTC"]["ask"], 0.082975)
        self.assertEqual(exchange._offline_markets["ETH/BTC"]["active"], True)

    def test_offline_tickers_fetch(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")
        tickers = list()
        for _ in exchange._offline_tickers:
            tickers.append(exchange._offline_fetch_tickers())

        self.assertEqual(len(tickers), 3)
        self.assertEqual(tickers[0]["ETH/BTC"]["bidVolume"], 10.011)
        self.assertEqual(tickers[1]["ETH/BTC"]["bidVolume"], 10.056)
        self.assertEqual(tickers[2]["ETH/BTC"]["bidVolume"], 10)

        with self.assertRaises(tkgtri.ExchangeWrapperOfflineFetchError) as cm:
            exchange._offline_fetch_tickers()

        e = cm.exception
        self.assertEqual(type(e), tkgtri.ExchangeWrapperOfflineFetchError)

    def test_offline_load_markets(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")
        markets = exchange._offline_load_markets()
        self.assertEqual(markets["ETH/BTC"]["active"], True)

        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")

        with self.assertRaises(tkgtri.ExchangeWrapperOfflineFetchError) as cm:
            exchange._offline_load_markets()

        e = cm.exception
        self.assertEqual(type(e), tkgtri.ExchangeWrapperOfflineFetchError)

    def test_offline_mode(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")

        markets = exchange.get_markets()
        tickers = exchange.get_tickers()

        self.assertEqual(tickers["ETH/BTC"]["bidVolume"], 10.011)
        self.assertEqual(len(tickers), len(markets))

    def test_offline_load_trades(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")
        exchange.offline_load_trades_from_file("test_data/orders_trades_kucoin.json")
        self.assertEqual(len(exchange._offline_trades), 3)
        trades = exchange.get_trades(None)
        self.assertListEqual(exchange._offline_trades, trades)

    def test_get_trades(self):

        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv",
                                  "test_data/orders_kucoin_multi.json")

        exchange.offline_load_trades_from_file("test_data/orders_trades_kucoin.json")

        # sell order
        order = tkgtri.TradeOrder.create_limit_order_from_start_amount("ETH/BTC", "ETH", 0.5, "BTC",
                                                                       0.06633157807472399)

        om = tkgtri.OrderManagerFok(order)
        om.fill_order(exchange)

        result = exchange.get_trades_results(order)
        self.assertEqual(result["filled"], 0.5)
        self.assertEqual(result["cost"], 0.03685088)
        self.assertEqual(result["dest_amount"], 0.03685088)
        self.assertEqual(result["src_amount"], 0.5)
        self.assertGreaterEqual(result["price"], 0.03685088/0.5)

        order.side = "buy"

        result = exchange.get_trades_results(order)
        self.assertEqual(result["filled"], 0.5)
        self.assertEqual(result["cost"], 0.03685088)
        self.assertEqual(result["dest_amount"], 0.5)
        self.assertEqual(result["src_amount"], 0.03685088)
        self.assertGreaterEqual(result["price"], 0.03685088 / 0.5)

    def test_precision(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")
        exchange.get_markets()
        symbol = "ETH/BTC"  # amount precision =3, price_precision = 6

        self.assertEqual(1.399, exchange.amount_to_precision(symbol, 1.399))
        self.assertEqual(1.399, exchange.amount_to_precision(symbol, 1.3999))

        self.assertEqual(1.399, exchange.price_to_precision(symbol, 1.399))
        self.assertEqual(1.3999, exchange.price_to_precision(symbol, 1.3999))
        self.assertEqual(1.123457, exchange.price_to_precision(symbol, 1.123456789))

        exchange.markets["ETH/BTC"] = None  # default precisions for price and amount 8

        self.assertEqual(1.12345678, exchange.amount_to_precision(symbol, 1.123456789))
        self.assertEqual(1.12345678, exchange.amount_to_precision(symbol, 1.123456789))

    @unittest.skip
    def test_precision_online(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.get_markets()
        symbol = "GNT/ETH"

        self.assertEqual(exchange.amount_to_precision(symbol, 1.3999999),
                         exchange._ccxt.amount_to_precision(symbol, 1.3999999))

        self.assertEqual(exchange.price_to_precision(symbol, 1.123456789),
                         exchange._ccxt.price_to_precision(symbol, 1.123456789)
                         )

    def test_create_order_book_array_from_ticker(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets_binance.json", "test_data/tickers_binance.csv")
        exchange.get_markets()
        exchange.get_tickers()

        ob_array = exchange._create_order_book_array_from_ticker(exchange.tickers["ETH/USDT"])
        self.assertEqual(ob_array["asks"], [[682.82, 99999999]])
        self.assertEqual(ob_array["bids"], [[682.5, 99999999]])


if __name__ == '__main__':
    unittest.main()
