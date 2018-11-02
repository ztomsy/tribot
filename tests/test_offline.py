# -*- coding: utf-8 -*-

from .context import tkgtri

import tkgcore
import unittest
import os
import glob
from subprocess import call
import tkgtri.analyzer as ta

# todo - tests for reports directories creation

class TriOfflineTestSuite(unittest.TestCase):
    """ TriBot Cli tests"""

    def _run_bot_offine(self, cli):
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
        orderbooks from ticker. result is good. start-qty = share_balance_to_bid * balance
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
        orderbooks from ticker. result is good. start-qty = share_balance_to_bid * balance
        :return:
        """

        cli = "--balance 1 offline --test -ob test_data/order_books.csv"
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.059392430685960465, float(deal.data_row["start-qty"]), 4)
        self.assertEqual(0.0028836493140395186, float(deal.data_row["result-fact-diff"]))

    def test_e2e_override_depth_amount_greater_than_from_order_book(self):
        """
        :return:
        """

        cli = "--balance 1 --override_depth_amount 0.5 offline  --test -ob test_data/order_books.csv "
        deal = self._run_bot_offine(cli)

        self.assertEqual(0.5, float(deal.data_row["_config_override_depth_amount"]), 4)
        self.assertEqual(0.5, float(deal.data_row["start-qty"]))

        self.assertEqual(float(deal.data_row["ob_result"]), float(deal.data_row["result"]))

    """
    Test cases: 
    
    - override_depth_amount less than from  Order book -> should going with the amount from order books  
    - override_depth_amount greater than max share of balance to bid 
    - skip order books
    -- with override_depth_amount, without depth_amount 
    --  
    """


if __name__ == '__main__':
    unittest.main()

