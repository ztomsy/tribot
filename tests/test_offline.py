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

    def test_offline_order_books(self):

        # default_config = "_config_default.json"
        # tribot = tkgtri.TriBot(default_config)
        #
        # cli = "offline -ob test_data/deals_28_ob.csv"
        #
        # tribot.set_from_cli(cli.split(" "))
        #
        # tribot.exchange.set_offline_mode(tribot.offline_markets_file, tribot.offline_tickers_file)
        #
        # tribot.as
        pass

    def test_offline_test_init(self):
        default_config = "_config_default.json"
        tribot = tkgtri.TriBot(default_config)

        tribot.exchange_id = "test"  # override
        path = "_{}".format(tribot.exchange_id)

        if not os.path.exists(path):
            os.mkdir(path)

        f = open(path+"/test.csv", "w+")
        f.write("test")
        f.close()

        f = open(path + "/test_ob.csv", "w+")
        f.write("test")
        f.close()

        f = open(path + "/test_m.json", "w+")
        f.write("test")
        f.close()

        num_files = len(glob.glob(path+"/test*"))
        self.assertEqual(3, num_files)

        tribot.init_test_run()

        num_files = len(glob.glob(path + "/test*"))

        self.assertEqual(0, num_files)
        self.assertEqual("test", tribot.deal_uuid)
        self.assertEqual("test", tribot.exchange_id)
        self.assertEqual(True, tribot.run_once)

    def test_e2e_general_mode(self):

        # orderbooks from ticker

        cli = "--balance 1 offline --test"

        call("python3 tribot.py {}".format(cli), shell=True)

        deal = ta.Deal()
        deal.load_from_csv("_test/test.csv", "test")

        #self.assertEqual()



if __name__ == '__main__':
    unittest.main()

