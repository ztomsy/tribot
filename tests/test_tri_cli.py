# -*- coding: utf-8 -*-

from .context import tkgtri

import tkgcore
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

    def test_cli_set_all_offline_files(self):

        cli = "offline --tickers tickers.csv"
        self.tribot.set_from_cli(cli.split(" "))
        self.assertEqual(self.tribot.offline, True)
        self.assertEqual(self.tribot.offline_tickers_file, "tickers.csv")


if __name__ == '__main__':
    unittest.main()


