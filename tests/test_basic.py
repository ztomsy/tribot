# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest


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

        # todo: test for cheching if log file created

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


if __name__ == '__main__':
    unittest.main()