# -*- coding: utf-8 -*-

from .context import tkgtri

import unittest
import os
import time
import uuid


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

        self.assertEqual(self.tribot.start_currency, ["ETH", "BTC"])
        self.assertEqual(self.tribot.test_balance, 1)

        self.assertEqual(self.tribot.api_key["apiKey"], "testApiKey")
        self.assertEqual(self.tribot.server_id, "PROD1")

        uuid_obj = uuid.UUID(self.tribot.session_uuid)

        self.assertEqual(self.tribot.session_uuid, str(uuid_obj))

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

    def test_reporter_init(self):
        self.tribot.load_config_from_file(self.default_config)

        self.assertEqual(self.tribot.influxdb["measurement"], "tri_status")
        self.tribot.init_remote_reports()

        self.assertEqual(self.tribot.reporter.def_indicators["session_uuid"], self.tribot.session_uuid)

        self.tribot.reporter.influx.set_tags(self.tribot.reporter.def_indicators)
        self.assertDictEqual(self.tribot.reporter.def_indicators, self.tribot.reporter.influx.tags)

        self.tribot.reporter.set_indicator("good_triangles", 100)

        self.assertDictEqual(self.tribot.reporter.indicators, dict({"good_triangles": 100}))

    @unittest.skip
    def test_reporter_push_data(self):
        self.tribot.load_config_from_file(self.default_config)
        self.tribot.init_remote_reports()
        self.tribot.reporter.set_indicator("good_triangles", 100)
        r = self.tribot.reporter.push_to_influx()
        self.assertEqual(r, True)

    def test_exchange_init(self):
        pass

    def test_tri_list(self):
        self.tribot.load_config_from_file(self.default_config)

        self.tribot.init_exchange()
        self.tribot.exchange.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        self.tribot.load_markets()
        self.tribot.set_triangles()
        self.tribot.fetch_tickers()
        self.tribot.fetch_tickers()
        self.tribot.proceed_triangles()

        check_tri = list(filter(lambda tri_dict: tri_dict['triangle'] == 'ETH-XEM-BTC', self.tribot.tri_list))[0]

        self.assertEqual(check_tri["symbol1"], "XEM/ETH")
        self.assertEqual(check_tri["leg1-price"], 0)
        self.assertEqual(check_tri["leg1-order"], "buy")

        self.assertEqual(check_tri["symbol2"], "XEM/BTC")
        self.assertEqual(check_tri["leg2-price"], 0.00003611)
        self.assertEqual(check_tri["leg2-order"], "sell")

        # from test_data/test_data.csv results without commission
        handmade_result = dict({"ETH-AMB-BNB": 0.9891723469,
                                "ETH-BNB-AMB": 1.0235943966,
                                "ETH-BTC-TRX": 1.0485521602,
                                "ETH-TRX-BTC": 0.9983509307,
                                "ETH-XEM-BTC": 0,
                                "ETH-BTC-XEM": 0,
                                "ETH-USDT-BTC": 0.9998017609,
                                "ETH-BTC-USDT": 0.999101801})

        # apply commission 0.0005 from config
        for i in self.tribot.tri_list:
            if i["triangle"] in handmade_result:
                if i["result"] is not None:
                    self.assertAlmostEqual(i["result"], handmade_result[i["triangle"]]*(1-self.tribot.commission)**3,
                                           delta=0.0001)
                else:
                    self.assertEqual(i["result"], handmade_result[i["triangle"]])

    def test_good_results(self):

        self.tribot.load_config_from_file(self.default_config)

        self.tribot.init_exchange()
        self.tribot.exchange.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        self.tribot.load_markets()
        self.tribot.set_triangles()
        self.tribot.fetch_tickers()
        self.tribot.fetch_tickers()  # 2nd fetch have good results
        self.tribot.proceed_triangles()

        good_results = self.tribot.get_good_triangles()

        good_triangles = ["ETH-BNB-AMB", "ETH-BTC-TRX", 'BTC-TRX-ETH']

        self.assertEqual(len(self.tribot.tri_list_good), len(good_triangles))

        for i in self.tribot.tri_list_good:
            self.assertIn(i["triangle"], good_triangles)

    def test_no_good_results(self):
        self.tribot.load_config_from_file(self.default_config)

        self.tribot.init_exchange()
        self.tribot.exchange.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        self.tribot.load_markets()
        self.tribot.set_triangles()
        self.tribot.fetch_tickers()
        self.tribot.proceed_triangles()

        good_results = self.tribot.get_good_triangles()

        self.assertEqual(good_results, 0)
        self.assertEqual(len(self.tribot.tri_list_good), 0)
        self.assertEqual(self.tribot.last_proceed_report["best_result"]["triangle"], 'BTC-ETH-USDT')


if __name__ == '__main__':
    unittest.main()