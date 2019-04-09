# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest
from subprocess import call
import tkgtri.analyzer as ta

# todo - tests for reports directories creation


class TriOfflineTestSuite(unittest.TestCase):
    """ TriBot Cli tests"""

    @staticmethod
    def _run_bot_offine(cli):
        """
        returns the deal loaded from the csv result file in _test/test.csv
        :param cli: cli parameters for bot
        :return: tkgtri.analyzer.Deal object
        """

        call("python3 tribot.py {}".format(cli), shell=True)
        deal = ta.Deal()
        deal.load_from_csv("_test/test.csv", "test")

        return deal

    def test_e2e_general_mode(self):
        """
        order books from ticker. result is good. start-qty should shrink to share_balance_to_bid * balance
        :return:
        """

        cli = "--balance 1 offline --test"
        deal = self._run_bot_offine(cli)

        self.assertEqual(float(deal.data_row["balance"]) * float(deal.data_row["_config_share_balance_to_bid"]),
                         float(deal.data_row["start-qty"]))

        self.assertEqual(0.8, float(deal.data_row["start-qty"]))
        self.assertEqual(0.03883667000000002, float(deal.data_row["result-fact-diff"]))

    def test_e2e_order_book_amount_less_than_max_bal(self):
        """
        orderbooks from ticker. result is good.
        1st leg order book depth = 2
        :return:
        """

        cli = "--balance 1 offline --test -ob test_data/order_books.csv"
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.05991321016925779, float(deal.data_row["start-qty"]), 4)
        self.assertEqual(0.0024007998307421993, float(deal.data_row["result-fact-diff"]))

        # prices from order book
        self.assertNotEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))

    def test_e2e_override_depth_amount_greater_than_from_order_book(self):
        """
        in this case override_depth_amount is greater than amount from order book, so the start quantity should be taken
        from override_depth_amount.
        Prices should be taken from tickers
        """

        cli = "--balance 1 --override_depth_amount 0.5 offline  --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.5, float(deal.data_row["_config_override_depth_amount"]), 4)
        self.assertEqual(0.5, float(deal.data_row["start-qty"]))
        self.assertEqual(float(deal.data_row["ob_result"]), float(deal.data_row["result"]))
        self.assertEqual(0.024282400000000093, float(deal.data_row["result-fact-diff"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_e2e_override_depth_amount_less_than_from_order_book(self):
        """
        in this case override_depth_amount is less than amount from order book, so the start quantity should be taken
        from order book. Results should be equal to test_e2e_order_book_amount_less_than_max_bal
        Prices should be taken from order books
        """

        cli = "--balance 1 --override_depth_amount 0.03 offline  --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.05991321016925779, float(deal.data_row["start-qty"]), 4)
        self.assertEqual(0.0024007998307421993, float(deal.data_row["result-fact-diff"]))

        # prices from order book
        self.assertNotEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))

    def test_e2e_override_depth_amount_greater_than_max_allowed_from_balance(self):
        """
        Case: override_depth_amount is greater than max share of balance to bid and amount from order book.
        Prices should be taken from tickers
        :return:
        """

        cli = "--balance 0.5 --override_depth_amount 0.5 offline  --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.5*0.8, float(deal.data_row["start-qty"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_skip_order_books_start_amount_max_from_balance(self):

        cli = "--balance 1 --skip_order_books offline --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.8, float(deal.data_row["start-qty"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_skip_order_books_override_depth_amount(self):

        cli = "--balance 1 --skip_order_books --override_depth_amount 0.5 offline --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.5, float(deal.data_row["start-qty"]))
        self.assertEqual(0.024282400000000093, float(deal.data_row["result-fact-diff"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_skip_order_books_general(self):
        cli = "--balance 1 --skip_order_books offline --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.8, float(deal.data_row["start-qty"]))
        self.assertEqual(0.03883667000000002, float(deal.data_row["result-fact-diff"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_skip_order_books_force_start_bid(self):
        cli = "--balance 1 --skip_order_books --force_start_bid 0.1 offline --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.1, float(deal.data_row["start-qty"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_skip_order_books_force_start_bid_and_override_depth(self):
        cli = "--balance 1 --skip_order_books --force_start_bid 0.1 --override_depth_amount 0.5 offline --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.5, float(deal.data_row["start-qty"]))

        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))

    def test_order_cancel_threshold(self):
        cli = "--config _config_default_ft.json --balance 1 --skip_order_books --force_start_bid 0.1  offline --test -t test_data/tickers_threshold.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.1, float(deal.data_row["start-qty"]))
        self.assertEqual("True", deal.data_row["_config_fullthrottle"])
        self.assertEqual(-0.01, float(deal.data_row["_config_cancel_price_threshold"]))

        self.assertAlmostEqual(0.4, float(deal.data_row["leg1-filled"]), 4)
        self.assertEqual(6, float(deal.data_row["leg1-order-updates"]))
        self.assertEqual("#below_threshold", deal.data_row["leg1-tags"])

        self.assertAlmostEqual(0.03397308998946259, float(deal.data_row["finish-qty"]), 6)


        # check if prices are from tickers
        self.assertEqual(float(deal.data_row["leg1-price"]), float(deal.data_row["leg1-ob-price"]))
        self.assertEqual(float(deal.data_row["leg2-price"]), float(deal.data_row["leg2-ob-price"]))
        self.assertEqual(float(deal.data_row["leg3-price"]), float(deal.data_row["leg3-ob-price"]))



    """
    Test cases: 
    
    x override_depth_amount less than from  Order book -> should going with the amount from order books  
    x override_depth_amount greater than max share of balance to bid 
    x skip order books
    xx with override_depth_amount less than  
    --  with force start_amount
    """


if __name__ == '__main__':
    unittest.main()

