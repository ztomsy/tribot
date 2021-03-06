from .context import tkgtri
from tkgtri import tri_arb as ta
from ztom import ccxtExchangeWrapper
import unittest
import json


class TriArbTestSuite(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        pass

    def tearDown(self):
        # self.tribot.dispose()
        pass

    def test_get_basic_triangles(self):

        markets = dict({"ETH/BTC": {"active": True, 'base': 'ETH', 'quote': 'BTC'},
                        "ADA/BTC": {"active": True, 'base': 'ADA', 'quote': 'BTC'},
                        "ADA/ETH": {"active": True, 'base': 'ADA', 'quote': 'ETH'},
                        "BNB/ETH": {"active": True, 'base': 'BNB', 'quote': 'ETH'},
                        "BNB/BTC": {"active": True, 'base': 'BNB', 'quote': 'BTC'}})

        # ex = ccxtExchangeWrapper.load_from_id("Exchange")
        # ex.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        #
        # markets = ex.get_markets()

        # check_triangle = list([['BTC', 'BNB', 'ETH'], ['BTC', 'ETH', 'BNB'], ['BTC', 'ETH', 'ADA'],
        # ['BTC', 'ADA', 'ETH']])

        triangles = ta.get_basic_triangles_from_markets(markets)

        check_triangle = list(
            [['ETH', 'BTC', 'ADA'], ['BTC', 'BNB', 'ETH']])

        self.assertEqual(len(triangles), len(check_triangle))

        for i in check_triangle:
            i.sort()
        check_triangle.sort()

        for i in triangles:
            i.sort()
        triangles.sort()

        self.assertEqual(len(triangles), len(check_triangle))
        self.assertListEqual(triangles, check_triangle)

    def test_get_all_triangles(self):

        markets = dict({"ETH/BTC": {"active": True, 'base': 'ETH', 'quote': 'BTC'},
                        "ADA/BTC": {"active": True, 'base': 'ADA', 'quote': 'BTC'},
                        "ADA/ETH": {"active": True, 'base': 'ADA', 'quote': 'ETH'},
                        "BNB/ETH": {"active": True, 'base': 'BNB', 'quote': 'ETH'},
                        "BNB/BTC": {"active": True, 'base': 'BNB', 'quote': 'BTC'}})

        triangles = ta.get_basic_triangles_from_markets(markets)

        start_currencies = ["ETH"]
        all_triangles = ta.get_all_triangles(triangles, start_currencies)
        check_triangles = list(
            [['ETH', 'BNB', 'BTC'], ['ETH', 'BTC', 'BNB'], ['ETH', 'BTC', 'ADA'], ['ETH', 'ADA', 'BTC']])

        self.assertEqual(len(all_triangles), len(check_triangles))
        for i in all_triangles:
            self.assertEqual(i in check_triangles, True)

        start_currencies = ["BTC"]
        all_triangles = ta.get_all_triangles(triangles, start_currencies)
        check_triangles = list(
            [['BTC', 'ETH', 'BNB'], ['BTC', 'BNB', 'ETH'], ['BTC', 'ADA', 'ETH'], ['BTC', 'ETH', 'ADA']])

        self.assertEqual(len(all_triangles), len(check_triangles))
        for i in all_triangles:
            self.assertEqual(i in check_triangles, True)

        start_currencies = ["BTC", "ETH"]
        all_triangles = ta.get_all_triangles(triangles, start_currencies)
        check_triangles = list(
            [['BTC', 'ETH', 'BNB'], ['BTC', 'BNB', 'ETH'], ['BTC', 'ADA', 'ETH'], ['BTC', 'ETH', 'ADA'],
             ['ETH', 'BNB', 'BTC'], ['ETH', 'BTC', 'BNB'], ['ETH', 'BTC', 'ADA'], ['ETH', 'ADA', 'BTC']])

        self.assertEqual(len(all_triangles), len(check_triangles))
        for i in all_triangles:
            self.assertEqual(i in check_triangles, True)

    def test_fill_triangles(self):
        start_currencies = ["ETH"]

        ex = ccxtExchangeWrapper.load_from_id("Exchange")
        ex.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")

        markets = ex.load_markets()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # none values for XEN in second fetch
        triangles = ta.get_basic_triangles_from_markets(markets)

        all_triangles = ta.get_all_triangles(triangles, start_currencies)

        tri_list = ta.fill_triangles(all_triangles, start_currencies, tickers)

        check_tri = list(filter(lambda tri_dict: tri_dict['triangle'] == 'ETH-XEM-BTC', tri_list))[0]

        self.assertEqual(check_tri["symbol1"], "XEM/ETH")
        self.assertEqual(check_tri["leg1-price"], 0)
        self.assertEqual(check_tri["leg1-order"], "buy")

        self.assertEqual(check_tri["symbol2"], "XEM/BTC")
        self.assertEqual(check_tri["leg2-price"], 0.00003611)
        self.assertEqual(check_tri["leg2-order"], "sell")

        # from test_data/test_data.csv
        handmade_result = dict({"ETH-AMB-BNB": 0.9891723469,
                                "ETH-BNB-AMB": 1.0235943966,
                                "ETH-BTC-TRX": 1.0485521602,
                                "ETH-TRX-BTC": 0.9983509307,
                                "ETH-XEM-BTC": 0,
                                "ETH-BTC-XEM": 0,
                                "ETH-USDT-BTC": 0.9998017609,
                                "ETH-BTC-USDT": 0.999101801})

        for i in tri_list:
            self.assertAlmostEqual(i["result"], handmade_result[i["triangle"]], delta=0.0001)

    def test_no_ticker(self):

        start_currencies = ["ETH"]

        ex = ccxtExchangeWrapper.load_from_id("Exchange")
        ex.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")

        markets = ex.load_markets()
        ex.fetch_tickers()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # none values for XEN in second fetch
        triangles = ta.get_basic_triangles_from_markets(markets)

        all_triangles = ta.get_all_triangles(triangles, start_currencies)

        tri_list = ta.fill_triangles(all_triangles, start_currencies, tickers)

        check_tri1 = list(filter(lambda x: x["triangle"] == "ETH-BTC-USDT", tri_list ))[0]

        self.assertEqual(check_tri1["result"], 0)
        self.assertEqual(check_tri1["symbol2"], "")
        self.assertEqual(check_tri1["leg2-order"], "")
        self.assertEqual(check_tri1["leg2-price"], 0)

        check_tri1 = list(filter(lambda x: x["triangle"] == "ETH-BTC-TRX", tri_list))[0]

        self.assertEqual(check_tri1["result"], 0)
        self.assertEqual(check_tri1["symbol3"], "TRX/ETH")
        self.assertEqual(check_tri1["leg3-order"], "sell")
        self.assertEqual(check_tri1["leg3-price"], 0)

    def test_best_recovery_amount_order2(self):
        # self.tribot.load_config_from_file(self.default_config)

        start_currency_filled = 1

        # partial fill params
        order2_amount = 4
        order2_filled = 3

        order2_recover_best_start_curr_amount = ta.order2_best_recovery_start_amount(start_currency_filled,
                                                                                     order2_amount,
                                                                                     order2_filled)

        self.assertEqual(1/4, order2_recover_best_start_curr_amount)

        # order 2 zero fill
        order2_amount = 4
        order2_filled = 0
        order2_recover_best_start_curr_amount = ta.order2_best_recovery_start_amount(start_currency_filled,
                                                                                     order2_amount,
                                                                                     order2_filled)
        self.assertEqual(1, order2_recover_best_start_curr_amount)

        # order 2 complete fill - no recovery
        order2_amount = 4
        order2_filled = 4
        order2_recover_best_start_curr_amount = ta.order2_best_recovery_start_amount(start_currency_filled,
                                                                                     order2_amount,
                                                                                     order2_filled)
        self.assertEqual(order2_recover_best_start_curr_amount, 0)

    def test_best_recovery_amount_order3(self):

        start_currency_filled = 1

        # filled half of order 2  (1/2 of start currency)
        order2_amount = 4
        order2_filled = 2

        order2_recover_best_start_curr_amount = ta.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)

        self.assertEqual(1/2, order2_recover_best_start_curr_amount)

        # order 3 partial fill
        order3_amount = 1/2
        order3_filled = 1/4

        order3_recover_best_start_curr_amount = ta.order3_best_recovery_start_amount(
            start_currency_filled, order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual((1/2 - 1/4), order3_recover_best_start_curr_amount)

        # order 3 fill
        order3_amount = 1/2
        order3_filled = 1/2

        order3_recover_best_start_curr_amount = ta.order3_best_recovery_start_amount(
            start_currency_filled, order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual(0, order3_recover_best_start_curr_amount)

        # order 3 zero fill
        order3_amount = 1 / 2
        order3_filled = 0

        order3_recover_best_start_curr_amount = ta.order3_best_recovery_start_amount(
            start_currency_filled, order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual(1/2 , order3_recover_best_start_curr_amount)


if __name__ == '__main__':
    unittest.main()