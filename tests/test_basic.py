# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest

# todo - tests for reports directories creation

class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):

        self.default_config = "_config_default.json"
        self.default_log = "_tri_log_default.log"

        self.tribot = tkgtri.TriBot(self.default_config, self.default_log)

    def tearDown(self):
        # self.tribot.dispose()
        pass

    def test_create_tribot(self):
        self.tribot.load_config_from_file(self.default_config)

        self.assertEqual(self.tribot.start_currency , "ETH")
        self.assertEqual(self.tribot.test_balance, 1)

        self.assertEqual(self.tribot.api_key["apiKey"], "testApiKey")

        # todo: test for checking if log file created

    def test_cli_overrides_config_file(self):

        self.tribot.debug = True
        self.tribot.live = True

        self.tribot.set_from_cli("--config _config_default.json --balance 2 --nodebug --nolive --exchange kraken".split(" "))

        self.tribot.load_config_from_file(self.tribot.config_filename)

        self.assertEqual(self.tribot.debug, False)
        self.assertEqual(self.tribot.live, False)

        self.assertEqual(self.tribot.exchange_id, "kraken")

        self.assertEqual(self.tribot.config_filename, "_config_default.json")
        self.assertEqual(self.tribot.test_balance, 2)

        self.assertEqual(self.tribot.api_key["apiKey"], "testApiKey")

    def test_multi_logging(self):

        self.tribot.log(self.tribot.LOG_ERROR, "ERRORS", list(("error line 1", "error line 2", "error line 3")))







if __name__ == '__main__':
    unittest.main()