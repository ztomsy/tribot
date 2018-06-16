# -*- coding: utf-8 -*-
from .context import tkgtri
from tkgtri import core
import unittest


class CoreFuncTestSuite(unittest.TestCase):

    def test_get_trade_direction_to_currency(self):
        symbol = "ETH/BTC"
        self.assertEqual("buy", core.get_trade_direction_to_currency(symbol, "ETH"))
        self.assertEqual("sell", core.get_trade_direction_to_currency(symbol, "BTC"))
        self.assertEqual(False, core.get_trade_direction_to_currency(symbol, "USD"))

    def test_get_symbol(self):
        markets = dict({"ETH/BTC": True})
        self.assertEqual("ETH/BTC", core.get_symbol("ETH", "BTC", markets))
        self.assertEqual("ETH/BTC", core.get_symbol("BTC", "ETH", markets))
        self.assertEqual(False, core.get_symbol("USD", "ETH", markets))

    def test_order_type(self):
        symbol = "ETH/BTC"
        self.assertEqual("buy", core.get_order_type("BTC", "ETH", symbol))
        self.assertEqual("sell", core.get_order_type("ETH", "BTC", symbol))
        self.assertEqual(False, core.get_order_type("BTC", "USD", symbol))


if __name__ == '__main__':
    unittest.main()