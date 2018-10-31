# -*- coding: utf-8 -*-

from .context import tkgtri

import tkgcore
import unittest
import os
import time
import uuid


# todo - tests for reports directories creation

class TriOfflineTestSuite(unittest.TestCase):
    """ TriBot Cli tests"""

    def test_offline_order_books(self):

        default_config = "_config_default.json"
        tribot = tkgtri.TriBot(default_config)

        cli = "offline -ob test_data/deals_28_ob.csv"

        tribot.set_from_cli(cli.split(" "))

        tribot.exchange.set_offline_mode(tribot.offline_markets_file, tribot.offline_tickers_file)

        tribot.as







if __name__ == '__main__':
    unittest.main()

