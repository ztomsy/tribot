# -*- coding: utf-8 -*-

from .context import tkgtri
from tkgtri import exchanges

import unittest

class ExchageWrapperTestSuite(unittest.TestCase):

    def test_create_wrapped(self):

        exchange = getattr(exchanges, "binance")
        exchange = exchange("binance")

        self.assertEqual(exchange.get_exchange_wrapper_id(), "binance")

    def test_create_generic(self):

        exchange = tkgtri.ccxtExchangeWrapper("kucoin")
        self.assertEqual(exchange.get_exchange_wrapper_id(), "generic")


if __name__ == '__main__':
    unittest.main()