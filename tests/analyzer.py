# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest
import ccxt


class AnalyzerTestSuite(unittest.TestCase):

    def test_counter_order(self):

        deal = tkgtri.Deal()
        deal.load_from_csv("./test_data/counter_order_tickers.csv", "9ee1d9dd-81fb-4e5a-bd9e-c085d7e6ffe5")

        r = tkgtri.Analyzer.find_counter_order_tickers(deal.all_tickers)
        self.assertEqual(r, {'leg2-counter-order-match-ticker': '256445'})

        r = tkgtri.Analyzer.find_counter_order_tickers(deal.all_tickers, 1)
        self.assertEqual(r, False)

    def test_maximum_start_amount(self):

        exchange = ccxt.binance()
        exchange.load_markets()
        launch_id = 28

        deal_file = "./test_data/deals_%s.csv" % launch_id
        tickers_file = "./test_data/deals_%s_tickers.csv" % launch_id
        ob_file = "./test_data/deals_%s_ob.csv" % launch_id

        deal = tkgtri.Deal()
        deal.load_from_csv(tickers_file, "17debfb7-17cc-4d0a-9e9c-ea19b63d3e98")
        deal.get_order_books_from_csv(ob_file)

        ob = dict()
        for i in range(1, 4):
            ob[i] = deal.order_books[deal.symbols[i - 1]]

        max_possible = tkgtri.Analyzer.get_maximum_start_amount(exchange, deal.data_row, ob, float(deal.data_row["bal-before"])*0.8, 10)

        self.assertEqual(max_possible, {'result': 0.005471840000000032, 'amount': 0.64426264})



if __name__ == '__main__':
    unittest.main()
