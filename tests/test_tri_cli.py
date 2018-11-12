# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest
import os
import time
import uuid


# todo - tests for reports directories creation

class TriCliTestSuite(unittest.TestCase):
    """ TriBot Cli tests"""

    def setUp(self):
        self.default_config = "_config_default.json"
        self.default_log = "_tri_log_default.log"
        self.tribot = tkgtri.TriBot(self.default_config, self.default_log)

    def test_cli_set_offline(self):

        cli = "offline"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.offline, True)


    def test_cli_set_all_offline_files(self):

        cli = "offline -t tickers.csv -ob ob.csv -m markets.json"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.offline, True)
        self.assertEqual(self.tribot.offline_tickers_file, "tickers.csv")
        self.assertEqual(self.tribot.offline_order_books_file, "ob.csv")
        self.assertEqual(self.tribot.offline_markets_file, "markets.json")

    def test_cli_set_offline_tickers(self):

        cli = "offline --tickers tickers.csv"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.offline, True)
        self.assertEqual(self.tribot.offline_tickers_file, "tickers.csv")

    def test_cli_deal_uuid(self):
        cli = "offline --deal 123456 -t tickers.csv -m markets.json -ob order_books.csv"

        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.offline, True)
        self.assertEqual(self.tribot.offline_deal_uuid, "123456")
        self.assertEqual(self.tribot.offline_markets_file, "markets.json")
        self.assertEqual(self.tribot.offline_tickers_file, "tickers.csv")
        self.assertEqual(self.tribot.offline_order_books_file, "order_books.csv")

    def test_cli_override_depth_amount(self):
        self.assertEqual(self.tribot.override_depth_amount, 0.0)

        cli = "--override_depth_amount 0.5"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.override_depth_amount, 0.5)

    def test_cli_skip_order_books(self):
        self.assertEqual(self.tribot.skip_order_books, False)
        cli = "--skip_order_books"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.skip_order_books, True)

    def test_cli_offline_test(self):
        self.assertEqual(self.tribot.offline, False)
        self.assertEqual(self.tribot.offline_run_test, False)

        cli = "offline --test"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(True, self.tribot.offline)
        self.assertEqual(True, self.tribot.offline_run_test)







if __name__ == '__main__':
    unittest.main()


