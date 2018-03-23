# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_create_tribot(self):

        tribot = tkgtri.triBot.create_from_config("_config-default.py")

        self.assertEqual(tribot.start_currency , "ETH")
        self.assertEqual(tribot.api_key["apiKey"], "testApiKey")


if __name__ == '__main__':
    unittest.main()