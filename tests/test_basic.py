# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest
import os
import time


# todo - tests for reports directories creation

class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_create_tribot(self):
        default_config = "_config_default.json"
        default_log = "_tri_log_default.log"

        tribot = tkgtri.TriBot(default_config,default_log)
        tribot.load_config_from_file(default_config)

        self.assertEqual(tribot.start_currency , "ETH")
        self.assertEqual(tribot.test_balance, 1)

        self.assertEqual(tribot.api_key["apiKey"], "testApiKey")

    def test_cli_overrides_config_file(self):

        default_config = "_config_default.json"
        default_log = "_tri_log_default.log"

        tribot = tkgtri.TriBot(default_config, default_log)

        tribot.debug = True
        tribot.live = True

        tribot.set_from_cli("--config _config_default.json --balance 2 --nodebug --nolive --exchange kraken".split(" "))

        tribot.load_config_from_file(tribot.config_filename)

        self.assertEqual(tribot.debug, False)
        self.assertEqual(tribot.live, False)

        self.assertEqual(tribot.exchange_id, "kraken")

        self.assertEqual(tribot.config_filename, "_config_default.json")
        self.assertEqual(tribot.test_balance, 2)

        self.assertEqual(tribot.api_key["apiKey"], "testApiKey")

    def test_logging(self):

        default_config = "_config_default.json"
        default_log = "_tri_log_default.log"

        tribot = tkgtri.TriBot(default_config, default_log)

        tribot.log(tribot.LOG_INFO, "Test")

        with open(default_log, 'r') as myfile:
            log_file = myfile.read()

        self.assertGreater(log_file.find("Test"), -1)

        os.remove(default_log)

    def test_timer(self):
        timer = tkgtri.Timer()
        timer.notch("start")
        time.sleep(0.1)
        timer.notch("finish")

        self.assertEqual(timer.notches[0]["name"], "start")
        self.assertAlmostEqual(timer.notches[1]["duration"], 0.1, 1)


if __name__ == '__main__':
    unittest.main()