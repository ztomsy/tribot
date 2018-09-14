# -*- coding: utf-8 -*-
from .context import tkgtri as tkg
import unittest


class OwaOrderManagerTestSuite(unittest.TestCase):

    def test_owa_manager_create(self):
        ex = tkg.ccxtExchangeWrapper.load_from_id("binance")
        order = tkg.RecoveryOrder("ETH/BTC", "ETH", 1, "BTC", 0.1)
        om = tkg.OwaManager(ex)
        om.add_order(order)
        om.set_order_supplementary_data(order, {"report_kpi": 1})
        self.assertEqual(om.supplementary[order.id]["report_kpi"], 1)

    def test_owa_manager_run_order(self):

        ex = tkg.ccxtExchangeWrapper.load_from_id("binance")
        ex.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        ex.get_markets()
        order1 = tkg.RecoveryOrder("ABC/XYZ", "ABC", 1, "XYZ", 0.1,
                                   ex.markets["ETH/BTC"]["limits"]["amount"]["min"]*1.01,
                                   max_best_amount_order_updates=2, max_order_updates=5)

        order2 = tkg.RecoveryOrder("USD/RUB", "USD", 1, "RUB", 70)
        om = tkg.OwaManager(ex)
        om.add_order(order1)
        om.add_order(order2)

        while len(om.get_open_orders()) > 0:
            om.proceed_orders()

        self.assertEqual("closed", order1.status)
        self.assertAlmostEqual(1, order1.filled, delta=0.0001)
        # self.assertEqual(0.1, order1.filled_dest_amount)
        self.assertAlmostEqual(1, order1.filled_start_amount, delta=0.00001)
        self.assertListEqual(list([order1]), om.get_closed_orders())

        om.proceed_orders()
        self.assertEqual(None, om.get_closed_orders())


if __name__ == '__main__':
    unittest.main()

