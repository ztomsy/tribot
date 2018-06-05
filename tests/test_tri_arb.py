from .context import tkgtri
from tkgtri import tri_arb as ta
from tkgtri import ccxtExchangeWrapper
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

        markets = ex.get_markets()
        ex.get_tickers()
        tickers = ex.get_tickers()  # none values for XEN in second fetch
        triangles = ta.get_basic_triangles_from_markets(markets)

        all_triangles = ta.get_all_triangles(triangles, start_currencies)

        tri_list = ta.fill_triangles(all_triangles, start_currencies, tickers)

        check_tri = list(filter(lambda tri_dict: tri_dict['triangle'] == 'ETH-XEM-BTC', tri_list))[0]

        self.assertEqual(check_tri["symbol1"], "XEM/ETH")
        self.assertEqual(check_tri["leg1-price"], None)
        self.assertEqual(check_tri["leg1-order"], "buy")

        self.assertEqual(check_tri["symbol2"], "XEM/BTC")
        self.assertEqual(check_tri["leg2-price"], 0.00003611)
        self.assertEqual(check_tri["leg2-order"], "sell")

        # from test_data/test_data.csv
        handmade_result = dict({"ETH-AMB-BNB": 0.9891723469,
                                "ETH-BNB-AMB": 1.0235943966,
                                "ETH-BTC-TRX": 1.0485521602,
                                "ETH-TRX-BTC": 0.9983509307,
                                "ETH-XEM-BTC": None,
                                "ETH-BTC-XEM": None,
                                "ETH-USDT-BTC": 0.9998017609,
                                "ETH-BTC-USDT": 0.999101801})

        for i in tri_list:
            self.assertAlmostEqual(i["result"], handmade_result[i["triangle"]], delta=0.0001)


if __name__ == '__main__':
    unittest.main()