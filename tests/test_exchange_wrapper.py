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

    def test_fetch_ticker_wrapped(self):
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



if __name__ == '__main__':
    unittest.main()