# -*- coding: utf-8 -*-

from .context import tkgtri
from tkgtri import Deal
from tkgtri import tri_arb as ta
import tkgcore
import unittest
import ccxt


class TriArbOrderBooksTestSuite(unittest.TestCase):

    # def test_counter_order(self):
    #     deal = Deal()
    #     deal.load_from_csv("./test_data/counter_order_tickers.csv", "9ee1d9dd-81fb-4e5a-bd9e-c085d7e6ffe5")
    #
    #     r = Analyzer.find_counter_order_tickers(deal.all_tickers)
    #     self.assertEqual(r, {'leg2-counter-order-match-ticker': '256445'})
    #
    #     r = Analyzer.find_counter_order_tickers(deal.all_tickers, 1)
    #     self.assertEqual(r, False)

    def test_maximum_start_amount(self):
        exchange = ccxt.binance()
        exchange.load_markets()
        launch_id = 28

        deal_file = "./test_data/deals_%s.csv" % launch_id
        tickers_file = "./test_data/deals_%s_tickers.csv" % launch_id
        ob_file = "./test_data/deals_%s_ob.csv" % launch_id

        deal = Deal()
        deal.load_from_csv(tickers_file, "17debfb7-17cc-4d0a-9e9c-ea19b63d3e98")
        deal.get_order_books_from_csv(ob_file)

        ob = dict()
        for i in range(1, 4):
            ob[i] = deal.order_books[deal.symbols[i - 1]]

        # within available volumes in order book
        max_possible = ta.get_maximum_start_amount(exchange, deal.data_row, ob,
                                                                 float(deal.data_row["bal-before"]) * 0.8, 10)

        self.assertEqual(max_possible, {'result': 1.0084931822214618, 'amount': 0.64426264})

        # start bid is very big
        max_possible = ta.get_maximum_start_amount(exchange, deal.data_row, ob,
                                                                 10, 100, 0.01)

        self.assertEqual( {'result': 1.0086905273264402, 'amount': 0.6154545454545455}, max_possible)


    def test_ob_results(self):

        exchange = tkgcore.ccxtExchangeWrapper.load_from_id("binance")
        exchange.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        exchange.get_markets()

        order_books_data = dict()
        order_books_data["ETH/BTC"] = dict()
        order_books_data["MANA/BTC"] = dict()
        order_books_data["MANA/ETH"] = dict()

        order_books_data["ETH/BTC"]["symbol"] = "ETH/BTC"
        order_books_data["ETH/BTC"]["asks"] = list(
            [[0.0712040000, 4.9020000000],
             [0.0712270000, 1.6860000000],
             [0.0712340000, 1.4230000000],
             [0.0712350000, 21.5900000000],
             [0.0712430000, 9.6350000000],
             [0.0712480000, 0.0200000000]]
        )

        order_books_data["ETH/BTC"]["bids"] = list(
            [[0.0711150000, 11.9230000000],
             [0.0711120000, 10.0000000000],
             [0.0711010000, 0.0840000000],
             [0.0710940000, 19.6610000000],
             [0.0710930000, 0.0180000000],
             [0.0710900000, 0.0010000000]]
        )

        order_books_data["MANA/BTC"]["symbol"] = "MANA/BTC"
        order_books_data["MANA/BTC"]["asks"] = list(
            [[0.0000200000, 18603122.0000000000],
             [0.0000229900, 929.0000000000],
             [0.0000232300, 11343.0000000000],
             [0.0000234500, 9452.0000000000],
             [0.0000243700, 182.0000000000],
             [0.0000250000, 3440682.0000000000],
             [0.0000250200, 41.0000000000],
             [0.0000250900, 41.0000000000]])

        order_books_data["MANA/BTC"]["bids"] = list(
            [[0.0000199900, 12632.0000000000],
             [0.0000199500, 3955.0000000000],
             [0.0000199000, 1070.0000000000],
             [0.0000198900, 21643.0000000000],
             [0.0000198800, 100000.0000000000],
             [0.0000198300, 1000.0000000000],
             [0.0000198000, 2771.0000000000],
             [0.0000197500, 130.0000000000]])

        order_books_data["MANA/ETH"]["symbol"] = "MANA/ETH"
        order_books_data["MANA/ETH"]["asks"] = list(
            [[0.0003533100, 7495.0000000000],
             [0.0003533200, 11321.0000000000],
             [0.0003599900, 3148.0000000000],
             [0.0003600000, 818.0000000000],
             [0.0003638600, 100.0000000000],
             [0.0003680000, 7785.0000000000],
             [0.0003700000, 421.0000000000],
             [0.0003713400, 3400.0000000000],
             [0.0003745000, 1286.0000000000],
             [0.0003745100, 1132.0000000000],
             [0.0003849300, 4826.0000000000]])

        order_books_data["MANA/ETH"]["bids"] = list(
            [[0.0003450100, 3113.0000000000],
             [0.0003450000, 12948.0000000000],
             [0.0003443000, 2729.0000000000],
             [0.0003432800, 2380.0000000000],
             [0.0003421900, 200.0000000000],
             [0.0003420500, 2925.0000000000],
             [0.0003400000, 45.0000000000],
             [0.0003390000, 777.0000000000],
             [0.0003300000, 29963.0000000000],
             [0.0003287100, 181.0000000000],
             [0.0003283400, 5062.0000000000]])

        order_books = dict()
        for key, ob in order_books_data.items():
            order_books[ob["symbol"]] = tkgcore.OrderBook(ob["symbol"], ob["asks"], ob["bids"])


        working_triangle = dict()

        working_triangle["symbol1"] = "ETH/BTC"
        working_triangle["symbol2"] = "MANA/BTC"
        working_triangle["symbol3"] = "MANA/ETH"

        # starting from ETH
        working_triangle["leg1-order"] = "sell"
        working_triangle["leg2-order"] = "buy"
        working_triangle["leg3-order"] = "sell"

        expected_result = ta.order_book_results(exchange, working_triangle,
                                                  {1: order_books[working_triangle["symbol1"]],
                                                   2: order_books[working_triangle["symbol2"]],
                                                   3: order_books[working_triangle["symbol3"]]},
                                                  5.4)
        self.assertAlmostEqual(1.23, expected_result["result"], 2 )

        # starting from BTC
        working_triangle["symbol1"] = "ETH/BTC"
        working_triangle["symbol2"] = "MANA/ETH"
        working_triangle["symbol3"] = "MANA/BTC"

        working_triangle["leg1-order"] = "buy"
        working_triangle["leg2-order"] = "buy"
        working_triangle["leg3-order"] = "sell"

        expected_result = ta.order_book_results(exchange, working_triangle,
                                                              {1: order_books[working_triangle["symbol1"]],
                                                               2: order_books[working_triangle["symbol2"]],
                                                               3: order_books[working_triangle["symbol3"]]},
                                                              0.1)

        self.assertAlmostEqual(0.79, expected_result["result"], 2)

        expected_result2 = ta.order_book_results(exchange, working_triangle,
                                                              {1: order_books[working_triangle["symbol1"]],
                                                               2: order_books[working_triangle["symbol2"]],
                                                               3: order_books[working_triangle["symbol3"]]},
                                                       10)

        self.assertEqual( expected_result2["result_amount"], 0.83153636)


if __name__ == '__main__':
    unittest.main()
