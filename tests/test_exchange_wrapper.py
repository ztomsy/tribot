# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest

class ExchageWrapperTestSuite(unittest.TestCase):

    def test_create_wrapped(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("binance")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "binance")
        self.assertEqual(exchange._ccxt.id, "binance")

    def test_create_generic(self):
        exchange = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "generic")


if __name__ == '__main__':
    unittest.main()