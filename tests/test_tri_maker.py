# -*- coding: utf-8 -*-
from .context import tkgtri
from tkgtri import SingleTriArbMaker
import tkgcore
from tkgcore import ccxtExchangeWrapper
from tkgcore import ActionOrder, ActionOrderManager, FokThresholdTakerPriceOrder, FokThresholdTakerPriceOrder

import unittest
import hashlib
import json


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

        maker = SingleTriArbMaker(currency1=good_triangle["cur1"],
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
                                  max_order3_updates=2000)

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

        self.assertEqual('fc8e8e363b736584d51462d100d9d0ad', hash)
        self.assertListEqual([["BTC", "TRX", "ETH"]], maker.current_triangle)

    def test_states_transition(self):

        ex = ccxtExchangeWrapper.load_from_id("binance")  #type: ccxtExchangeWrapper
        ex.set_offline_mode("test_data/markets.json", "test_data/tickers_maker.csv")
        ex.load_markets()
        ex.fetch_tickers()
        tickers = ex.fetch_tickers()  # second fetch contains good triangle

        om = ActionOrderManager(ex)

        good_triangle = self.good_triangle

        maker = SingleTriArbMaker(currency1=good_triangle["cur1"],
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
                                  max_order3_updates=2000)

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

        om.add_order(maker.order3)
        om.proceed_orders()
        maker.update_state(tickers)

        self.assertEqual("order3", maker.state)

        while len(om.get_open_orders()) > 0:
            om.proceed_orders()
            maker.update_state(tickers)

        self.assertEqual("finished", maker.state)







if __name__ == '__main__':
    unittest.main()
