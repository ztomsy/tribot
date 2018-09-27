# -*- coding: utf-8 -*-

from .context import tkgtri

import tkgcore
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
        # self.assertEqual(self.tribot.test_balance, 1)

        self.assertEqual(self.tribot.api_key["apiKey"], "testApiKey")
        self.assertEqual(self.tribot.server_id, "PROD1")

        uuid_obj = uuid.UUID(self.tribot.session_uuid)

        self.assertEqual(self.tribot.session_uuid, str(uuid_obj))

        # todo: test for checking if log file created

    def test_cli_overrides_config_file(self):

        self.tribot.debug = True
        self.tribot.force_best_tri = True

        self.tribot.set_from_cli("--config _config_default.json --balance 2 --debug --force --exchange kraken "
                                 "--runonce --force_start_bid 666 --noauth".split(" "))

        self.tribot.load_config_from_file(self.tribot.config_filename)

        self.assertEqual(self.tribot.debug, True)
        self.assertEqual(self.tribot.run_once, True)
        self.assertEqual(self.tribot.force_best_tri, True)
        self.assertEqual(self.tribot.noauth, True)

        self.assertEqual(self.tribot.exchange_id, "kraken")

        self.assertEqual(self.tribot.config_filename, "_config_default.json")
        self.assertEqual(self.tribot.test_balance, 2)
        self.assertEqual(self.tribot.force_start_amount, 666)

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
        timer = tkgcore.Timer()
        timer.notch("start")
        time.sleep(0.1)
        timer.notch("finish")

        self.assertEqual(timer.notches[0]["name"], "start")
        self.assertAlmostEqual(timer.notches[1]["duration"], 0.1, 1)

    def test_reporter_init(self):
        self.tribot.load_config_from_file(self.default_config)

        self.assertEqual(self.tribot.influxdb["measurement"], "tri_status")
        self.tribot.init_remote_reports()

        self.tribot.reporter.influx.set_tags(self.tribot.reporter.def_indicators)
        self.assertDictEqual(self.tribot.reporter.def_indicators, self.tribot.reporter.influx.tags)

        self.tribot.reporter.set_indicator("good_triangles", 100)
        self.tribot.reporter.set_indicator("session_uuid", 6666)

        self.assertDictEqual(self.tribot.reporter.indicators, dict({"good_triangles": 100, "session_uuid": 6666}))

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

        self.tribot.tri_list_good = self.tribot.get_good_triangles()

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

        self.assertEqual(len(good_results), 0)
        self.assertEqual(len(self.tribot.tri_list_good), 0)
        self.assertEqual(self.tribot.last_proceed_report["best_result"]["triangle"], 'BTC-ETH-USDT')

    def test_get_max_balance_to_bid(self):
        self.tribot.load_config_from_file(self.default_config)

        self.assertEqual(self.tribot.get_max_balance_to_bid("ETH", 1, 1.006, 1.006), 1)
        self.assertEqual(self.tribot.get_max_balance_to_bid("ETH", 20, 1.006, 1.006), 5)
        self.assertEqual(self.tribot.get_max_balance_to_bid("ETH", 20, 1.01, 1.01), 10)

        self.assertEqual(self.tribot.get_max_balance_to_bid("BTC", 1, 1.001, 1.001), None)  # threshold too low
        self.assertEqual(self.tribot.get_max_balance_to_bid("BTC", 1, 1.005, 1.005), 0.5)   # 1st threshold
        self.assertEqual(self.tribot.get_max_balance_to_bid("BTC", 0.7, 1.01, 1.01), 0.7)   # 2nd threshold
        self.assertEqual(self.tribot.get_max_balance_to_bid("BTC", 2, 1.01, 1.01), 1)       # 2nd max balance cap

    def test_best_recovery_amount_order2(self):

        start_currency_filled = 1

        # partial fill params
        order2_amount = 4
        order2_filled = 3

        order2_recover_best_start_curr_amount = self.tribot.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)
        self.assertEqual(order2_recover_best_start_curr_amount, 1/4)

        # order 2 zero fill
        order2_amount = 4
        order2_filled = 0
        order2_recover_best_start_curr_amount = self.tribot.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)
        self.assertEqual(order2_recover_best_start_curr_amount, 1)

        # order 2 complete fill - no recovery
        order2_amount = 4
        order2_filled = 4
        order2_recover_best_start_curr_amount = self.tribot.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)
        self.assertEqual(order2_recover_best_start_curr_amount, 0)

    def test_best_recovery_amount_order3(self):

        start_currency_filled = 1

        # filled half of order 2  (1/2 of start currency)
        order2_amount = 4
        order2_filled = 2

        order2_recover_best_start_curr_amount = self.tribot.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)

        self.assertEqual(order2_recover_best_start_curr_amount, 1/2)

        # order 3 partial fill
        order3_amount = 1/2
        order3_filled = 1/4

        order3_recover_best_start_curr_amount = self.tribot.order3_best_recovery_start_amount(
            start_currency_filled,order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual(1/2 - 1/4, order3_recover_best_start_curr_amount)

        # order 3 fill
        order3_amount = 1/2
        order3_filled = 1/2

        order3_recover_best_start_curr_amount = self.tribot.order3_best_recovery_start_amount(
            start_currency_filled, order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual(0, order3_recover_best_start_curr_amount)

        # order 3 zero fill
        order3_amount = 1 / 2
        order3_filled = 0

        order3_recover_best_start_curr_amount = self.tribot.order3_best_recovery_start_amount(
            start_currency_filled, order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual(1/2, order3_recover_best_start_curr_amount)


if __name__ == '__main__':
    unittest.main()