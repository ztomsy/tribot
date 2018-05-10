from .context import tkgtri
from tkgtri import stats_influx
import unittest
import json


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_tags(self):
        deal_row = {"server-id" : "Arb2",

                    'BNB-after': '41.78100931', 'BNB-before': 41.78100931,
                    'after-start': 26125.586834,
                    'bal-after': 89.49255701,
                    'bal-before': 89.49255701,
                    'cur1': 'ETH',
                    'cur2': 'AION',
                    'cur3': 'BNB',
                    'dbg': 0,
                    'deal-id': 12,
                    'deal-uuid': '8091d4cf-e3b5-4b14-b935-ce3eb94de12c',
                    'good_cons_results': 2,
                    'leg-orders': 'buy-sell-sell',
                    'leg1-counter-price': 0.004198,
                    'leg1-counter-qty': 2192.64,
                    'leg1-fills': 1,
                    'leg1-namnt': 242.87600366,
                    'leg1-ob-price': 0.0042,
                    'leg1-order': 'buy',
                    'leg1-price': 0.0042,
                    'leg1-price-fact': 0.0042,
                    'leg1-price-type': "ask",
                    'leg1-qty': 57855.17000000,
                    'leg1-result': 204.19,
                    'leg1-time-from-ticker': 0.073,
                    'leg2-counter-price': 0.22271,
                    'leg2-counter-qty': 62.68,
                    'leg2-fills': 8,
                    'leg2-namnt': 0.18517378,
                    'leg2-ob-price': 0.22174,
                    'leg2-order': 'sell',
                    'leg2-price': 0.22195,
                    'leg2-price-fact': 0.21914777511141587,
                    'leg2-price-type': 'bid',
                    'leg2-qty': 44.11000000,
                    'leg2-result': 44.747784200000005,
                    'leg2-time-from-ticker': 0.128,
                    'leg3-counter-price': 0.019208,
                    'leg3-counter-qty': 3.75,
                    'leg3-fills': 1,
                    'leg3-namnt': 3.96872784,
                    'leg3-ob-price': 0.019206,
                    'leg3-order': 'sell',
                    'leg3-price': 0.019206,
                    'leg3-price-fact': 0.019206,
                    'leg3-price-type': 'bid',
                    'leg3-qty': 206.64000000,
                    'leg3-result': 0.85927644,
                    'leg3-time-from-ticker': 0.174,
                    'min-namnt': 0.18517378,
                    'ob_result': 1.0102222492929291,
                    'res-amnt': 0.18765955013311186,
                    'result': 1.0134239854752214,
                    'result-fact': 0.85927644,
                    'result-fact-diff': 0.0016784400000000588,
                    'result-fact-pp': 0.2,
                    'result-precise': 1.0128258908469656,
                    'start-qty': 0.857598,
                    'status': 'Ok',
                    'symbol1': 'AION/ETH',
                    'symbol2': 'AION/BNB',
                    'symbol3': 'BNB/ETH',
                    'tags': '#bal_reduce#incrStart',
                    'ticker': 434614,
                    'time-start': '2018-05-10 09:49:37.077615',
                    'timestamp': '2018-05-10 17:05:02.664449',
                    'triangle': 'ETH-AION-BNB'}

        stats_db = stats_influx.TkgStatsInflux("13.231.173.161", 8086, "tkg_dev", "tri_deals_results")
        tags = list(["deal-uuid", "server-id"])

        tags_dict = dict()
        for i in tags:
            tags_dict[i] = deal_row[i]

        stats_db.set_tags(tags)
        self.assertEqual(stats_db.tags, tags)

        stats_data = stats_db.extract_tags_and_fields(deal_row)

        self.assertDictEqual(stats_data["tags"], tags_dict)

        for i in range(1, len(tags)+1):
            self.assertNotIn(tags[i-1], stats_data["fields"])

    @unittest.skip
    def test_put_deal_info(self):
        stats_db = stats_influx.TkgStatsInflux("13.231.173.161", 8086, "tkg_dev", "tri_deals_results")
        tags = list(["deal-uuid", "server-id"])
        stats_db.set_tags(tags)

        deal_row = {"server-id": "Arb2",

                    'BNB-after': '41.78100931', 'BNB-before': 41.78100931,
                    'after-start': 26125.586834,
                    'bal-after': 89.49255701,
                    'bal-before': 89.49255701,
                    'cur1': 'ETH',
                    'cur2': 'AION',
                    'cur3': 'BNB',
                    'dbg': 0,
                    'deal-id': 12,
                    'deal-uuid': '8091d4cf-e3b5-4b14-b935-ce3eb94de12c',
                    'good_cons_results': 2,
                    'leg-orders': 'buy-sell-sell',
                    'leg1-counter-price': 0.004198,
                    'leg1-counter-qty': 2192.64,
                    'leg1-fills': 1,
                    'leg1-namnt': 242.87600366,
                    'leg1-ob-price': 0.0042,
                    'leg1-order': 'buy',
                    'leg1-price': 0.0042,
                    'leg1-price-fact': 0.0042,
                    'leg1-price-type': "ask",
                    'leg1-qty': 57855.17000000,
                    'leg1-result': 204.19,
                    'leg1-time-from-ticker': 0.073,
                    'leg2-counter-price': 0.22271,
                    'leg2-counter-qty': 62.68,
                    'leg2-fills': 8,
                    'leg2-namnt': 0.18517378,
                    'leg2-ob-price': 0.22174,
                    'leg2-order': 'sell',
                    'leg2-price': 0.22195,
                    'leg2-price-fact': 0.21914777511141587,
                    'leg2-price-type': 'bid',
                    'leg2-qty': 44.11000000,
                    'leg2-result': 44.747784200000005,
                    'leg2-time-from-ticker': 0.128,
                    'leg3-counter-price': 0.019208,
                    'leg3-counter-qty': 3.75,
                    'leg3-fills': 1,
                    'leg3-namnt': 3.96872784,
                    'leg3-ob-price': 0.019206,
                    'leg3-order': 'sell',
                    'leg3-price': 0.019206,
                    'leg3-price-fact': 0.019206,
                    'leg3-price-type': 'bid',
                    'leg3-qty': 206.64000000,
                    'leg3-result': 0.85927644,
                    'leg3-time-from-ticker': 0.174,
                    'min-namnt': 0.18517378,
                    'ob_result': 1.0102222492929291,
                    'res-amnt': 0.18765955013311186,
                    'result': 1.0134239854752214,
                    'result-fact': 0.85927644,
                    'result-fact-diff': 0.0016784400000000588,
                    'result-fact-pp': 0.2,
                    'result-precise': 1.0128258908469656,
                    'start-qty': 0.857598,
                    'status': 'Ok',
                    'symbol1': 'AION/ETH',
                    'symbol2': 'AION/BNB',
                    'symbol3': 'BNB/ETH',
                    'tags': '#bal_reduce#incrStart',
                    'ticker': 434614,
                    'time-start': '2018-05-10 09:49:37.077615',
                    'timestamp': '2018-05-10 17:05:02.664449',
                    'triangle': 'ETH-AION-BNB'}

        stats_db.write_deal_info(deal_row)





if __name__ == '__main__':
    unittest.main()
