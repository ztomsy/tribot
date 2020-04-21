# -*- coding: utf-8 -*-

from .context import tkgtri

import ztom
import unittest
import os
import time
import uuid
import glob
import datetime


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

        self.assertEqual(self.tribot.start_currency, ["ETH", "BTC", "USDT"])
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

        handlers = tribot.logger.handlers[:]
        for handler in handlers:
            handler.close()
            tribot.logger.removeHandler(handler)

        os.remove(default_log)

    def test_timer(self):
        timer = ztom.Timer()
        timer.notch("start")
        time.sleep(0.1)
        timer.notch("finish")

        self.assertEqual(timer.notches[0]["name"], "start")
        self.assertAlmostEqual(timer.notches[1]["duration"], 0.1, 1)

    @unittest.skip
    def test_reporter_push_data(self):
        self.tribot.load_config_from_file(self.default_config)
        self.tribot.init_remote_reports()
        self.tribot.reporter.set_indicator("good_triangles", 100)
        r = self.tribot.reporter.push_to_influx()
        self.assertEqual(r, True)

    def test_config_report(self):
        self.tribot.load_config_from_file(self.default_config)
        config_report = self.tribot.get_config_report()

        self.assertEqual(25, config_report["_config_order_update_total_requests"])


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

    def test_good_results_ignore_currency(self):

        self.tribot.load_config_from_file(self.default_config)

        self.tribot.init_exchange()
        self.tribot.exchange.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
        self.tribot.load_markets()
        self.tribot.set_triangles()
        self.tribot.fetch_tickers()
        self.tribot.fetch_tickers()  # 2nd fetch have good results
        self.tribot.proceed_triangles()

        # first set of ignore
        self.tribot.ignore_currency = list(["AMB", "BNB"])
        self.tribot.tri_list_good = self.tribot.get_good_triangles()

        # good_triangles = ["ETH-BNB-AMB", "ETH-BTC-TRX", 'BTC-TRX-ETH'] good triangle without ignore option

        good_triangles = ["ETH-BTC-TRX", 'BTC-TRX-ETH']

        self.assertEqual(len(self.tribot.tri_list_good), len(good_triangles))

        for i in self.tribot.tri_list_good:
            self.assertIn(i["triangle"], good_triangles)
            self.assertNotIn(i["triangle"], ["ETH-BNB-AMB"])

        # second set of ignore
        self.tribot.ignore_currency = list(["TRX"])
        self.tribot.tri_list_good = self.tribot.get_good_triangles()

        # good triangle without ignore option
        # good_triangles = ["ETH-BNB-AMB", "ETH-BTC-TRX", 'BTC-TRX-ETH']

        good_triangles = ["ETH-BNB-AMB"]
        self.assertEqual(len(self.tribot.tri_list_good), len(good_triangles))

        for i in self.tribot.tri_list_good:
            self.assertIn(i["triangle"], good_triangles)
            self.assertNotIn(i["triangle"], ["ETH-BTC-TRX", 'BTC-TRX-ETH'])

        # third set of ignore and not exist currency
        self.tribot.ignore_currency = list(["TRX", "BTC", "ETH", "AMB", "XYZ"])
        self.tribot.tri_list_good = self.tribot.get_good_triangles()

        # good triangle without ignore option
        # good_triangles = ["ETH-BNB-AMB", "ETH-BTC-TRX", 'BTC-TRX-ETH']

        self.assertEqual(0, len(self.tribot.tri_list_good))

        for i in self.tribot.tri_list_good:
            self.assertIn(i["triangle"], good_triangles)
            self.assertNotIn(i["triangle"], ["ETH-BTC-TRX", 'BTC-TRX-ETH'])

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

        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("ETH", 1, 1.006, 1.006), 1)
        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("ETH", 20, 1.006, 1.006), 5)
        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("ETH", 20, 1.01, 1.01), 10)

        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("BTC", 1, 1.001, 1.001), None)  # threshold too low
        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("BTC", 1, 1.005, 1.005), 0.5)   # 1st threshold
        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("BTC", 0.7, 1.01, 1.01), 0.7)   # 2nd threshold
        self.assertEqual(self.tribot.max_balance_to_bid_from_thresholds("BTC", 2, 1.01, 1.01), 1)       # 2nd max balance cap

        self.assertEqual(2, self.tribot.max_balance_to_bid_from_thresholds("USDT", 2, 1.01, 1.01))
        self.assertEqual(100, self.tribot.max_balance_to_bid_from_thresholds("USDT", 120, 1.01, 1.01))
        self.assertEqual(None, self.tribot.max_balance_to_bid_from_thresholds("USDT", 120, 1, 1))

    def test_best_recovery_amount_order2(self):
        self.tribot.load_config_from_file(self.default_config)

        start_currency_filled = 1

        # partial fill params
        order2_amount = 4
        order2_filled = 3

        order2_recover_best_start_curr_amount = self.tribot.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)
        self.assertEqual(1/4 * self.tribot.recover_factor, order2_recover_best_start_curr_amount,)

        # order 2 zero fill
        order2_amount = 4
        order2_filled = 0
        order2_recover_best_start_curr_amount = self.tribot.order2_best_recovery_start_amount(start_currency_filled,
                                                                                              order2_amount,
                                                                                              order2_filled)
        self.assertEqual(1 * self.tribot.recover_factor, order2_recover_best_start_curr_amount)

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

        self.assertEqual(1/2 * self.tribot.recover_factor, order2_recover_best_start_curr_amount)

        # order 3 partial fill
        order3_amount = 1/2
        order3_filled = 1/4

        order3_recover_best_start_curr_amount = self.tribot.order3_best_recovery_start_amount(
            start_currency_filled, order2_amount, order2_filled, order3_amount, order3_filled)

        self.assertEqual((1/2 - 1/4) * self.tribot.recover_factor, order3_recover_best_start_curr_amount)

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

        self.assertEqual(1/2 * self.tribot.recover_factor , order3_recover_best_start_curr_amount)

    @unittest.skip
    def test_order_books_save(self):
        self.tribot.load_config_from_file(self.default_config)

        order_books_data = dict()
        order_books_data["ETH/BTC"] = dict()
        order_books_data["MANA/BTC"] = dict()
        order_books_data["MANA/ETH"] = dict()

        order_books_data["ETH/BTC"]["symbol"] = "ETH/BTC"
        order_books_data["ETH/BTC"]["asks"] = list(
            [[0.0712040000, 4.9020000000],
             [0.0712270000, 1.6860000000],
             [0.0712340000, 1.4230000000],
             [0.0712350000, 21.5900000000],
             [0.0712430000, 9.6350000000],
             [0.0712480000, 0.0200000000]]
        )

        order_books_data["ETH/BTC"]["bids"] = list(
            [[0.0711150000, 11.9230000000],
             [0.0711120000, 10.0000000000],
             [0.0711010000, 0.0840000000],
             [0.0710940000, 19.6610000000],
             [0.0710930000, 0.0180000000],
             [0.0710900000, 0.0010000000]]
        )

        order_books_data["MANA/BTC"]["symbol"] = "MANA/BTC"
        order_books_data["MANA/BTC"]["asks"] = list(
            [[0.0000200000, 18603122.0000000000],
             [0.0000229900, 929.0000000000],
             [0.0000232300, 11343.0000000000],
             [0.0000234500, 9452.0000000000],
             [0.0000243700, 182.0000000000],
             [0.0000250000, 3440682.0000000000],
             [0.0000250200, 41.0000000000],
             [0.0000250900, 41.0000000000]])

        order_books_data["MANA/BTC"]["bids"] = list(
            [[0.0000199900, 12632.0000000000],
             [0.0000199500, 3955.0000000000],
             [0.0000199000, 1070.0000000000],
             [0.0000198900, 21643.0000000000],
             [0.0000198800, 100000.0000000000],
             [0.0000198300, 1000.0000000000],
             [0.0000198000, 2771.0000000000],
             [0.0000197500, 130.0000000000]])

        order_books_data["MANA/ETH"]["symbol"] = "MANA/ETH"
        order_books_data["MANA/ETH"]["asks"] = list(
            [[0.0003533100, 7495.0000000000],
             [0.0003533200, 11321.0000000000],
             [0.0003599900, 3148.0000000000],
             [0.0003600000, 818.0000000000],
             [0.0003638600, 100.0000000000],
             [0.0003680000, 7785.0000000000],
             [0.0003700000, 421.0000000000],
             [0.0003713400, 3400.0000000000],
             [0.0003745000, 1286.0000000000],
             [0.0003745100, 1132.0000000000],
             [0.0003849300, 4826.0000000000]])

        order_books_data["MANA/ETH"]["bids"] = list(
            [[0.0003450100, 3113.0000000000],
             [0.0003450000, 12948.0000000000],
             [0.0003443000, 2729.0000000000],
             [0.0003432800, 2380.0000000000],
             [0.0003421900, 200.0000000000],
             [0.0003420500, 2925.0000000000],
             [0.0003400000, 45.0000000000],
             [0.0003390000, 777.0000000000],
             [0.0003300000, 29963.0000000000],
             [0.0003287100, 181.0000000000],
             [0.0003283400, 5062.0000000000]])


        order_books = dict()
        for key, ob in order_books_data.items():
            order_books[ob["symbol"]] = ztom.OrderBook(ob["symbol"], ob["asks"], ob["bids"])

        self.tribot.save_order_books(str(uuid.uuid4()), order_books)

    def _prepare_bot_for_test_start_amount(self):
        import test_data.order_books_data as td  # getting sample order books

        self.tribot.load_config_from_file(self.default_config)
        self.tribot.init_exchange()
        self.tribot.exchange.offline = True

        working_triangle = dict()
        working_triangle["result"] = 1.006
        working_triangle["ob_result"] = 1.006

        working_triangle["symbol1"] = "ETH/BTC"
        working_triangle["symbol2"] = "MANA/BTC"
        working_triangle["symbol3"] = "MANA/ETH"

        working_triangle["leg1-order"] = "sell"
        working_triangle["leg2-order"] = "buy"
        working_triangle["leg3-order"] = "sell"

        order_books_data = td.get_order_books()

        order_books = dict()
        for key, ob in order_books_data.items():
            order_books[ob["symbol"]] = ztom.OrderBook(ob["symbol"], ob["asks"], ob["bids"])

        return (order_books, working_triangle)

    def test_start_amount_default_parameters(self):
        order_books, working_triangle = self._prepare_bot_for_test_start_amount()

        self.tribot.balance = 1
        self.tribot.start_currency = ["BTC"]
        bal_to_bid = self.tribot.start_amount_to_bid(working_triangle, order_books)
        self.assertEqual(0.5, bal_to_bid)

        # balance is less than in config
        self.tribot.balance = 0.5
        # bal_to_bid = self.tribot.start_amount_to_bid(working_triangle, order_books)
        # self.assertEqual(0.5*self.tribot.share_balance_to_bid, bal_to_bid)

        # results less than thresholds
        self.tribot.balance = 0.5
        working_triangle["result"] = 0.99
        working_triangle["ob-result"] = 0.99

        bal_to_bid = self.tribot.start_amount_to_bid(working_triangle, order_books)
        self.assertEqual(None, bal_to_bid)

    def test_start_amount_force_best_tri(self):
        order_books, working_triangle = self._prepare_bot_for_test_start_amount()

        self.tribot.balance = 1
        self.tribot.start_currency = ["BTC"]
        working_triangle["result"] = 0.99  # this should be ignored and results will be taken from config
        working_triangle["ob-result"] = 0.99

        bal_to_bid = self.tribot.start_amount_to_bid(working_triangle, order_books, True)
        self.assertEqual(0.5, bal_to_bid)

        # balance is less than in config
        self.tribot.balance = 0.5
        bal_to_bid = self.tribot.start_amount_to_bid(working_triangle, order_books, True)
        self.assertEqual(0.5, bal_to_bid)

    def test_start_amount_force_start_bid(self):

        order_books, working_triangle = self._prepare_bot_for_test_start_amount()

        self.tribot.balance = 10
        self.tribot.force_best_tri = False
        self.tribot.force_start_amount = 6
        # working_triangle["result"] = 0.99  # this should be ignored and results will be taken from config
        # working_triangle["ob-result"] = 0.99

        bal_to_bid = self.tribot.start_amount_to_bid(working_triangle, order_books, self.tribot.force_best_tri,
                                                     self.tribot.force_start_amount)

        self.assertEqual(6, bal_to_bid)

    def test_restrict_amount_to_bid_from_order_book_default_parameters_short_ob(self):

        order_books, working_triangle = self._prepare_bot_for_test_start_amount()

        order_books_data_2 = {"asks": list([[0.0000200000, 100]]), "bids":  list([[0.0000200000, 100]])}
        order_books["MANA/BTC"] = ztom.OrderBook("MANA/BTC", order_books_data_2["asks"], order_books_data_2["bids"])

        self.tribot.balance = 1
        bal_to_bid = 5

        expected_result, ob_result, bid_from_order_book = self.tribot.restrict_amount_to_bid_from_order_book(
            bal_to_bid, working_triangle, order_books)

        self.assertAlmostEqual(1.2268, expected_result, 4)
        self.assertAlmostEqual(0.02812, bid_from_order_book, 4)

    def test_restrict_amount_to_bid_from_order_book_default_parameters_longer_ob(self):
        order_books, working_triangle = self._prepare_bot_for_test_start_amount()

        order_books_data_2 = {"asks": list([[0.0000200000, 100],
                                            [0.0000300000, 100]]),
                              "bids": list([[0.0000200000, 100]])}

        order_books["MANA/BTC"] = ztom.OrderBook("MANA/BTC", order_books_data_2["asks"], order_books_data_2["bids"])

        self.tribot.balance = 1
        bal_to_bid = 5

        expected_result, ob_result, bid_from_order_book = self.tribot.restrict_amount_to_bid_from_order_book(
            bal_to_bid, working_triangle, order_books, True)

        self.assertAlmostEqual(0.02, bid_from_order_book, 4)

        # start amount is less (0.02 vs 0.028) because in case of short order book from  previous test case
        # (test_restrict_amount_to_bid_from_order_book_default_parameters_short_ob) the last checked amount
        # of order book is the max available amount in order book (0.028) which has the better price than the result of
        # max available amount in bigger OB (~0.029) which has the lesser result

    def test_restrict_amount_to_bid_from_order_book_force_start_tri(self):
        order_books, working_triangle = self._prepare_bot_for_test_start_amount()

        order_books_data_2 = {"asks": list([[0.0000200000, 10],
                                            [0.0000300000, 100]]),
                              "bids": list([[0.0000200000, 100]])}

        order_books["MANA/BTC"] = ztom.OrderBook("MANA/BTC", order_books_data_2["asks"], order_books_data_2["bids"])

        self.tribot.balance = 1
        bal_to_bid = 5

        # should return None for everything because OB results are less than threshold
        self.assertEqual((None, None, None), self.tribot.restrict_amount_to_bid_from_order_book(
            bal_to_bid, working_triangle, order_books, False)  )

        expected_result, ob_result, bid_from_order_book = self.tribot.restrict_amount_to_bid_from_order_book(
            bal_to_bid, working_triangle, order_books, True)

        self.assertAlmostEqual(0.02, bid_from_order_book, 4)

    def test_finalize_start_amount(self):

        self.tribot.load_config_from_file(self.default_config)

        self.tribot.balance = 1
        self.assertEqual(0.8, self.tribot.finalize_start_amount(1))
        self.assertEqual(0.6, self.tribot.finalize_start_amount(0.6))

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

    def test_fullthrottle_init(self):
        self.tribot.load_config_from_file(self.tribot.config_filename)
        self.assertEqual(False, self.tribot.fullthrottle["enabled"])
        self.assertEqual([0, 50], self.tribot.fullthrottle["start_at"])

    def test_update_state(self):

        # fullthrottle not enabled
        timestamp = 0
        current_state = "go"
        lap_time = 60
        prev_throttle_start_timestamp = 0
        fullthrottle_enabled = False
        start_at = [0, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("go", new_state)

        # fullthrottle enabled - earlier - on start
        timestamp = 0
        current_state = "wait"
        lap_time = 60
        prev_throttle_start_timestamp = 0
        fullthrottle_enabled = True
        start_at = [0, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("go", new_state)

        # fullthrottle enabled - earlier - timestamp nor fits

        timestamp = datetime.datetime(2019, 1, 1, 13, 1, 1).timestamp()
        current_state = "wait"
        lap_time = 60
        prev_throttle_start_timestamp = 0
        fullthrottle_enabled = True
        start_at = [0, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("wait", new_state)

        # fullthrottle enabled - earlier - timestamp not fits
        timestamp = datetime.datetime(2019, 1, 1, 13, 1, 59).timestamp()
        current_state = "wait"
        lap_time = 60
        prev_throttle_start_timestamp = 0
        fullthrottle_enabled = True
        start_at = [0, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("wait", new_state)

        # fullthrottle enabled - earlier - timestamp is good
        timestamp = datetime.datetime(2019, 1, 1, 13, 1, 0).timestamp()
        current_state = "wait"
        lap_time = 60
        prev_throttle_start_timestamp = 0
        fullthrottle_enabled = True
        start_at = [00, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("go", new_state)

        # fullthrottle enabled - next start earlier than lap time - timestamp is good
        timestamp = datetime.datetime(2019, 1, 1, 13, 1, 50).timestamp()
        current_state = "wait"
        lap_time = 60
        prev_throttle_start_timestamp = datetime.datetime(2019, 1, 1, 13, 1, 50).timestamp() - 10
        fullthrottle_enabled = True
        start_at = [00, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("wait", new_state)

        # fullthrottle enabled - from go to wait - no transition
        timestamp = datetime.datetime(2019, 1, 1, 13, 1, 1).timestamp()
        current_state = "go"
        lap_time = 60
        prev_throttle_start_timestamp = datetime.datetime(2019, 1, 1, 13, 1, 1).timestamp() - 50
        fullthrottle_enabled = True
        start_at = [00, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("go", new_state)

        # fullthrottle enabled - from go to wait transition OK
        timestamp = 1549480450.999999
        current_state = "go"
        lap_time = 60
        prev_throttle_start_timestamp = timestamp - 61
        fullthrottle_enabled = True
        start_at = [0, 50]

        new_state = self.tribot.update_state(current_state, timestamp, fullthrottle_enabled, start_at,
                                             lap_time, prev_throttle_start_timestamp)

        self.assertEqual("wait", new_state)

    def test_seconds_from_timestamp(self):
        timestamp = 1549480450.999999
        self.assertEqual(True, self.tribot.check_time_to_launch([10], timestamp))
        self.assertEqual(False, self.tribot.check_time_to_launch([0, 5], timestamp))

    def test_do_trade(self):
        self.tribot.load_config_from_file(self.tribot.config_filename)

        self.tribot.init_exchange()
        self.tribot.init_offline_mode()
        self.tribot.load_markets()
        self.tribot.init_order_manager()

        self.assertEqual(0, self.tribot.orders_settings["1"]["time_to_cancel"])
        self.assertEqual(600, self.tribot.orders_settings["2"]["time_to_cancel"])

        order = self.tribot.do_trade(1, "ETH/BTC", "BTC", "ETH",1, "buy", 0.1, 0)
        self.assertEqual(0, self.tribot.orders_settings["1"]["time_to_cancel"])
        self.assertIsInstance(self.tribot.order_manager.get_closed_orders()[-1], ztom.FokOrder)

        self.tribot.cancel_price_threshold = 0.001
        order = self.tribot.do_trade(2, "ETH/BTC", "BTC", "ETH", 1, "buy", 0.1, 0)
        self.assertEqual(600, self.tribot.orders_settings["2"]["time_to_cancel"])
        self.assertIsInstance(self.tribot.order_manager.get_closed_orders()[-1], ztom.FokThresholdTakerPriceOrder)


if __name__ == '__main__':
    unittest.main()