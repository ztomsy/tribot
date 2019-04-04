# -*- coding: utf-8 -*-
from .context import tkgtri
from tkgtri import SingleTriArbMakerDeal, TriArbMakerCollection
import tkgcore
from tkgcore import ccxtExchangeWrapper
from tkgcore import ActionOrder, ActionOrderManager, FokThresholdTakerPriceOrder, FokThresholdTakerPriceOrder

import unittest
import hashlib
import json
import copy


def hash_of_object_values(data):

    # data = ['only', 'lists', [1,2,3], 'dictionaries', {'a':0,'b':1}, 'numbers', 47, 'strings']
    data_md5 = hashlib.md5(json.dumps(vars(data), sort_keys=True).encode('utf-8')).hexdigest()
    return data_md5


class SingleTriArbMakerTestSuite(unittest.TestCase):
    def setUp(self):
        self.good_triangle = {'leg3-order': 'sell', 'leg3-price-type': 'bid', 'leg3-price': 0.082923,
                         'triangle': 'BTC-TRX-ETH', 'result': 1.0474554803405187, 'cur2': 'TRX',
                         'leg3-cur1-qty': 0.833873688, 'leg2-price-type': 'bid', 'leg1-price-type': 'bid',
                         'leg-orders': 'buy-sell-sell', 'leg2-price': 0.00012, 'leg1-order': 'buy',
                         'leg3-ticker-qty': 10.056, 'leg1-ticker-qty': 200.0, 'leg1-price': 9.48e-06,
                         'leg2-ticker-qty': 725.0, 'leg2-order': 'sell', 'leg1-cur1-qty': 0.0018960000000000001,
                         'cur1': 'BTC', 'symbol2': 'TRX/ETH', 'symbol1': 'TRX/BTC', 'cur3': 'ETH',
                         'leg2-cur1-qty': 0.08700000000000001, 'symbol3': 'ETH/BTC'}

    def test_create(self):

        good_triangle = self.good_triangle

        maker = SingleTriArbMakerDeal(currency1=good_triangle["cur1"],
                                      currency2=good_triangle["cur2"],
                                      currency3=good_triangle["cur3"],
                                      price1=good_triangle["leg1-price"],
                                      price2=good_triangle["leg2-price"],
                                      price3=good_triangle["leg3-price"],
                                      start_amount=0.01,
                                      min_amount_currency1=0.003,
                                      symbol1=good_triangle["symbol1"],
                                      symbol2=good_triangle["symbol2"],
                                      symbol3=good_triangle["symbol3"],
                                      commission=0.00075,
                                      commission_maker=0.0006,
                                      threshold=1.001,
                                      max_order1_updates=2000,
                                      max_order2_updates=2000,
                                      max_order3_updates=2000,
                                      uuid="test")



        self.assertIsNone(maker.order1)
        self.assertIsNone(maker.order2)
        self.assertIsNone(maker.order3)

        self.assertEqual(0.00075, maker.commission)
        self.assertEqual(0.0006, maker.commission_maker)

        self.assertEqual(1.001, maker.threshold)

        self.assertEqual(0.0, maker.leg2_recovery_target)
        self.assertEqual(0.0, maker.leg2_recovery_amount)

        self.assertEqual(0.0, maker.leg3_recovery_target)
        self.assertEqual(0.0, maker.leg3_recovery_amount)

        self.assertEqual("test", maker.uuid)


        self.assertListEqual([["BTC", "TRX", "ETH"]], maker.current_triangle)

        self.assertEqual("", maker.status)
        self.assertEqual(0, maker.filled_start_amount)
        self.assertEqual(0, maker.result_amount)
        self.assertEqual(0, maker.gross_profit)

        hash = hash_of_object_values(maker)
        """
        hash 90a06b8f25ef95d728c2a8f2f89142f0 created for this set of data:

                good_triangle = {'leg3-order': 'sell', 'leg3-price-type': 'bid', 'leg3-price': 0.082923,
                        'triangle': 'BTC-TRX-ETH', 'result': 1.0474554803405187, 'cur2': 'TRX',
                        'leg3-cur1-qty': 0.833873688, 'leg2-price-type': 'bid', 'leg1-price-type': 'bid',
                        'leg-orders': 'buy-sell-sell', 'leg2-price': 0.00012, 'leg1-order': 'buy',
                        'leg3-ticker-qty': 10.056, 'leg1-ticker-qty': 200.0, 'leg1-price': 9.48e-06,
                        'leg2-ticker-qty': 725.0, 'leg2-order': 'sell', 'leg1-cur1-qty': 0.0018960000000000001,
                        'cur1': 'BTC', 'symbol2': 'TRX/ETH', 'symbol1': 'TRX/BTC', 'cur3': 'ETH',
                        'leg2-cur1-qty': 0.08700000000000001, 'symbol3': 'ETH/BTC'}

                                  currency1=good_triangle["cur1"],
                                  currency2=good_triangle["cur2"],
                                  currency3=good_triangle["cur3"],
                                  price1=good_triangle["leg1-price"],
                                  price2=good_triangle["leg2-price"],
                                  price3=good_triangle["leg3-price"],
                                  start_amount=0.01,
                                  min_amount_currency1=0.003,
                                  symbol1=good_triangle["symbol1"],
                                  symbol2=good_triangle["symbol2"],
                                  symbol3=good_triangle["symbol3"],
                                  commission=0.00075,
                                  commission_maker=0.0006,
                                  threshold=1.001,
                                  max_order1_updates=2000,
                                  max_order2_updates=2000,
                                  max_order3_updates=2000        
        """
        self.assertEqual('c9affde94535d353f937ed138083bf0c', hash)

    def test_run_ok(self):

        ex = ccxtExchangeWrapper.load_from_id("binance")  # type: ccxtExchangeWrapper
        ex.set_offline_mode("test_data/markets.json", "test_data/tickers_maker.csv")
        ex.load_markets()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # second fetch contains good triangle

        om = ActionOrderManager(ex)

        good_triangle = self.good_triangle

        maker = SingleTriArbMakerDeal(currency1=good_triangle["cur1"],
                                      currency2=good_triangle["cur2"],
                                      currency3=good_triangle["cur3"],
                                      price1=good_triangle["leg1-price"],
                                      price2=good_triangle["leg2-price"],
                                      price3=good_triangle["leg3-price"],
                                      start_amount=0.01,
                                      min_amount_currency1=0.003,
                                      symbol1=good_triangle["symbol1"],
                                      symbol2=good_triangle["symbol2"],
                                      symbol3=good_triangle["symbol3"],
                                      commission=0.00075,
                                      commission_maker=0.0006,
                                      threshold=1.001,
                                      max_order1_updates=2000,
                                      max_order2_updates=2000,
                                      max_order3_updates=2000,
                                      )

        self.assertEqual("new", maker.state)

        maker.update_state(tickers)

        self.assertEqual("order1_create", maker.state)

        self.assertEqual("TRX/BTC", maker.order1.symbol)
        self.assertEqual(good_triangle["leg1-price"], maker.order1.price)
        self.assertEqual("buy", maker.order1.side)

        om.add_order(maker.order1)
        self.assertEqual("open", maker.order1.status)

        om.proceed_orders()
        self.assertEqual("open", maker.order1.status)

        maker.update_state(tickers)
        self.assertEqual("order1", maker.state)

        while len(om.get_open_orders()) > 0:

            # !!!!
            # first we proceed the orders and we update the deal manager with new updated orders
            om.proceed_orders()
            maker.update_state(tickers)

        # order1 is closed
        # second order creation phase
        self.assertEqual("order2_create", maker.state)

        # adding order2 and proceed
        om.add_order(maker.order2)
        om.proceed_orders()
        maker.update_state(tickers)

        self.assertEqual("order2", maker.state)

        while len(om.get_open_orders()) > 0:
            om.proceed_orders()
            maker.update_state(tickers)

        self.assertEqual("order3_create", maker.state)
        self.assertEqual(0, maker.leg2_recovery_amount)
        self.assertEqual(0, maker.leg2_recovery_target)

        om.add_order(maker.order3)
        om.proceed_orders()
        maker.update_state(tickers)

        self.assertEqual("order3", maker.state)

        while len(om.get_open_orders()) > 0:
            om.proceed_orders()
            maker.update_state(tickers)

        self.assertEqual("finished", maker.state)

        self.assertEqual(0, maker.leg3_recovery_amount)
        self.assertEqual(0, maker.leg3_recovery_target)

        self.assertEqual("OK", maker.status)

        self.assertEqual(0.01, maker.filled_start_amount)

        self.assertAlmostEqual((0.01) * good_triangle["result"], maker.result_amount, 4)
        self.assertAlmostEqual((0.01) * good_triangle["result"] - 0.01, maker.gross_profit, 4)

    def test_failed_leg1(self):
        ex = ccxtExchangeWrapper.load_from_id("binance")  #type: ccxtExchangeWrapper

        ex.set_offline_mode("test_data/markets.json", "test_data/tickers_maker.csv")

        ex.load_markets()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # second fetch contains good triangle

        om = ActionOrderManager(ex)

        om.offline_order_updates = 10

        good_triangle = self.good_triangle

        maker = SingleTriArbMakerDeal(currency1=good_triangle["cur1"],
                                      currency2=good_triangle["cur2"],
                                      currency3=good_triangle["cur3"],
                                      price1=good_triangle["leg1-price"],
                                      price2=good_triangle["leg2-price"],
                                      price3=good_triangle["leg3-price"],
                                      start_amount=0.01,
                                      min_amount_currency1=0.003,
                                      symbol1=good_triangle["symbol1"],
                                      symbol2=good_triangle["symbol2"],
                                      symbol3=good_triangle["symbol3"],
                                      commission=0.00075,
                                      commission_maker=0.0006,
                                      threshold=1.001,
                                      max_order1_updates=2000,
                                      max_order2_updates=2000,
                                      max_order3_updates=2000,
                                      uuid="test"
                                      )

        maker.update_state(tickers)
        om.add_order(maker.order1)

        om.proceed_orders()
        maker.update_state(tickers)

        maker.order1.force_close()

        om.proceed_orders()
        maker.update_state(tickers)

        self.assertEqual("Failed", maker.status)

        self.assertEqual(0, maker.leg2_recovery_amount)
        self.assertEqual(0, maker.leg2_recovery_target)

        self.assertEqual(0, maker.leg3_recovery_amount)
        self.assertEqual(0, maker.leg3_recovery_target)

        self.assertEqual(0, maker.filled_start_amount)
        self.assertEqual(0, maker.result_amount)
        self.assertEqual(0, maker.gross_profit)


    def test_failed_leg2(self):
        ex = ccxtExchangeWrapper.load_from_id("binance")  #type: ccxtExchangeWrapper

        ex.set_offline_mode("test_data/markets.json", "test_data/tickers_maker.csv")

        ex.load_markets()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # second fetch contains good triangle

        om = ActionOrderManager(ex)

        om.offline_order_updates = 10

        good_triangle = self.good_triangle

        maker = SingleTriArbMakerDeal(currency1=good_triangle["cur1"],
                                      currency2=good_triangle["cur2"],
                                      currency3=good_triangle["cur3"],
                                      price1=good_triangle["leg1-price"],
                                      price2=good_triangle["leg2-price"],
                                      price3=good_triangle["leg3-price"],
                                      start_amount=0.01,
                                      min_amount_currency1=0.003,
                                      symbol1=good_triangle["symbol1"],
                                      symbol2=good_triangle["symbol2"],
                                      symbol3=good_triangle["symbol3"],
                                      commission=0.00075,
                                      commission_maker=0.0006,
                                      threshold=1.001,
                                      max_order1_updates=2000,
                                      max_order2_updates=2000,
                                      max_order3_updates=2000,
                                      uuid="test"
                                      )

        maker.update_state(tickers)
        om.add_order(maker.order1)

        while len(om.get_open_orders()) > 0:
            om.proceed_orders()
            maker.update_state(tickers)

        om.add_order(maker.order2)
        om.proceed_orders()
        maker.update_state(tickers)

        maker.order2.force_close()
        om.proceed_orders()
        maker.update_state(tickers)

        self.assertEqual("InRecovery", maker.status)

        self.assertEqual(1054.8523206751054, maker.leg2_recovery_amount)
        self.assertEqual(0.01, maker.leg2_recovery_target)

        self.assertEqual(0, maker.leg3_recovery_amount)
        self.assertEqual(0, maker.leg3_recovery_target)

        self.assertEqual(0.01, maker.filled_start_amount)
        self.assertEqual(0, maker.result_amount)
        self.assertEqual(-0.01, maker.gross_profit)

    def test_recovery(self):
        ex = ccxtExchangeWrapper.load_from_id("binance")  #type: ccxtExchangeWrapper

        ex.set_offline_mode("test_data/markets.json", "test_data/tickers_maker.csv")

        ex.load_markets()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # second fetch contains good triangle

        om = ActionOrderManager(ex)

        om.offline_order_updates = 10

        good_triangle = self.good_triangle

        maker = SingleTriArbMakerDeal(currency1=good_triangle["cur1"],
                                      currency2=good_triangle["cur2"],
                                      currency3=good_triangle["cur3"],
                                      price1=good_triangle["leg1-price"],
                                      price2=good_triangle["leg2-price"],
                                      price3=good_triangle["leg3-price"],
                                      start_amount=0.01,
                                      min_amount_currency1=0.003,
                                      symbol1=good_triangle["symbol1"],
                                      symbol2=good_triangle["symbol2"],
                                      symbol3=good_triangle["symbol3"],
                                      commission=0.00075,
                                      commission_maker=0.0006,
                                      threshold=1.001,
                                      max_order1_updates=2000,
                                      max_order2_updates=2000,
                                      max_order3_updates=2000,
                                      uuid="test"
                                      )

        maker.update_state(tickers)
        om.add_order(maker.order1)

        while len(om.get_open_orders()) > 0:
            # !!!!
            # first we proceed the orders and we update the deal manager with new updated orders
            om.proceed_orders()
            maker.update_state(tickers)

        om.add_order(maker.order2)
        om.proceed_orders()  # this will create order

        while maker.order2.get_active_order().update_requests_count < 6:
            om.proceed_orders()  # this will fill order once for 1/10 of amount
            maker.update_state(tickers)

        print("")
        print("Force Cancel")
        print("")

        # let's force to close the order
        maker.order2.force_close()
        om.proceed_orders()

        maker.update_state(tickers)

        self.assertEqual("closed", maker.order2.status)
        self.assertLess(maker.order2.filled, maker.order2.amount)
        self.assertLess(0, maker.leg2_recovery_amount)
        self.assertLess(0, maker.leg2_recovery_target)

        self.assertEqual(maker.leg2_recovery_amount,  maker.order2.amount_start - maker.order2.filled_start_amount)
        self.assertAlmostEqual(0.5 * maker.order2.amount, maker.leg2_recovery_amount, 6)

        self.assertAlmostEqual(1/2, maker.order2.filled / maker.order2.amount, 6)
        self.assertAlmostEqual(0.005, maker.leg2_recovery_target, 6)

        # proceed to leg3

        self.assertEqual("order3_create", maker.state)
        om.add_order(maker.order3)

        while maker.order3.get_active_order().update_requests_count < 6:
            om.proceed_orders()  # this will fill order once for 1/10 of amount
            maker.update_state(tickers)

        # let's force to close the order
        maker.order3.force_close()
        om.proceed_orders()

        maker.update_state(tickers)

        self.assertEqual(maker.leg3_recovery_amount,  maker.order3.amount_start - maker.order3.filled_start_amount)

        self.assertAlmostEqual(1 / 2, maker.order3.filled / maker.order3.amount, 6)
        self.assertAlmostEqual(0.0025, maker.leg3_recovery_target, 6)
        self.assertAlmostEqual(0.5 * maker.order3.amount, maker.leg3_recovery_amount, 6)

        self.assertEqual("finished", maker.state)

        self.assertEqual("InRecovery", maker.status)
        self.assertEqual(0.01, maker.filled_start_amount)

        self.assertAlmostEqual((0.01/4) * good_triangle["result"], maker.result_amount, 4)
        self.assertAlmostEqual((0.01 / 4) * good_triangle["result"] - 0.01, maker.gross_profit, 4)

    class SingleTriArbMakerTestSuite(unittest.TestCase):

        def test_collection_add_remove(self):

            triarb1 = SingleTriArbMakerDeal("CUR1", "CUR2", "CUR3",
                                           1, 2, 3, 0.1, 0.001, "CUR1CUR2", "CUR2/CUR3", "CUR3/CUR1", 0.0007,
                                           0.0007, 1.0005, uuid="test1")

            triarb2 = SingleTriArbMakerDeal("CUR1", "CUR2", "CUR3",
                                            1, 2, 3, 0.1, 0.001, "CUR1CUR2", "CUR2/CUR3", "CUR3/CUR1", 0.0007,
                                            0.0007, 1.0005, uuid="test2")

            tri_collection = TriArbMakerCollection(max_deals=3)

            self.assertEqual(True, tri_collection.add_deal(triarb1))
            self.assertEqual(True, tri_collection.add_deal(triarb2))

            self.assertListEqual([triarb1, triarb2], tri_collection.deals)

            # removing OK
            self.assertEqual(True, tri_collection.remove_deal("test1"))
            self.assertListEqual([triarb2], tri_collection.deals)

            # removing not OK
            with self.assertRaises(Exception) as e:
                tri_collection.remove_deal("test666")
                self.assertEqual(e.args[0], "Deal with uuid {} not found".format("test666"))

            # adding not OK
            with self.assertRaises(Exception) as e:
                tri_collection.add_deal(triarb2)
                self.assertEqual(e.args[0], "Deal with uuid {} is already exists".format("test2"))

            self.assertListEqual([triarb2], tri_collection.deals)

            tri_collection.add_deal(triarb1)

            triarb3 = copy.deepcopy(triarb1)
            triarb3.uuid = "test3"

            tri_collection.add_deal(triarb3)

            self.assertListEqual([triarb2, triarb1, triarb3], tri_collection.deals)

            tri_collection.remove_deal("test1")

            self.assertListEqual([triarb2, triarb3], tri_collection.deals)

            # exceed max_deals
            tri_collection.add_deal(triarb1)

            triarb4 = copy.deepcopy(triarb1)
            triarb4.uuid = "test4"

            with self.assertRaises(Exception) as e:
                tri_collection.add_deal(triarb4)
                self.assertEqual(e.args[0], "Max deals number {} exceeded".format(3))

                self.assertListEqual([triarb2, triarb3, triarb1], tri_collection.deals)

            # empty uuid
            tri_collection.remove_deal("test1")
            triarb1.uuid = ""

            with self.assertRaises(Exception) as e:
                tri_collection.add_deal(triarb1)
                self.assertEqual(e.args[0], "Empty uuid")


if __name__ == '__main__':
    unittest.main()
