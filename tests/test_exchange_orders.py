# -*- coding: utf-8 -*-
from .context import tkgtri
from tkgtri.exchange_order import exchangeOrder
from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
import datetime
import unittest


class ExchangeOrderTestSuite(unittest.TestCase):

    def setUp(self):
        self.ew = ccxtExchangeWrapper.load_from_id("binance")
        self.eo = exchangeOrder(self.ew)

    def test_exchange_order_create(self):
        self.assertEqual(self.ew, self.eo.exchange_wrapper)

    def test_update_order_from_exchange(self):

        order_resp = dict({
            'id': "test_id",
            'timestamp': datetime.datetime.now(),
            'symbol': "ETH/BTC",
            'type': "limit",
            'side': "buy",
            'amount': 1,
            'filled': None,
            'remaining': None,
            'price': 666,
            'cost': 222,
            'status': 'open',
            'fee': None,
            'trades': None
        })

        self.ew.markets = dict({"ETH/BTC": True})

        self.eo.order = TradeOrder.create_limit_order_from_start_amount(self.eo.exchange_wrapper.markets, "BTC", 1,
                                                                        "ETH", 0.07)

        self.eo.update_order_from_exchange(order_resp)
        pass


if __name__ == '__main__':
    unittest.main()
