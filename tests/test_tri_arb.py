from .context import tkgtri
from tkgtri import tri_arb as ta
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


    def test_fill_triangles(self):
        start_currencies = ["ETH", "BTC"]
        triangles = list(
            [['ETH', 'BTC', 'ADA'], ['BTC', 'BNB', 'ETH']])

        with open('tests/tickers.json') as f:
            ccxt_tickers = json.load(f)

        ta.fill_triangles(triangles, start_currencies, ccxt_tickers)

        pass


if __name__ == '__main__':
    unittest.main()