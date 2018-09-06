#
# utility to trace order execution
# orders are saved to test_data/orders/<exchange_id>_<num>.json
#

import tkgtri
import sys
import json
import collections

from tkgtri.trade_manager import *

_keys = {"binance":
             {"key": "M1lHFjmqzixs1S8IqST9lXP2DvzJuqNTR4lgpuv1PmutDTwxIAXRdjayTTVOR3SX",
              "secret": "Scov95f2UtBmtDb8J8PsWGXxVohNzWGC50CebPkriRHV1M6S6KVqYforOLNRYYXE"},
         "kucoin":
             {"key": "5b3f8876cbdbf7242da8c517",
              "secret": "135e2242-30ce-4552-9d0e-74264e041200"}
         }

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("binance",
#                                              "AmEkXUlAh3fW1XkxIOSLovMVia1B55bWI2937Y9ZGRu25uJj2XSCBbOGoI8bb8II",
#                                              "6yy8vrkUR3aOBJyUkzRtEHGYR01gxMmyYJ6jMHyt3HxY7AtXlKr54FmtPOLUsBvh")

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin",
#                                              "5b22b10709e5a14f2c125e3d", "11ec0073-8919-4863-a518-7e2468506752")

exchange_id = "kucoin"
start_curr = "ETH"
dest_cur = "TEL"
# start_curr_amount = 0.05 / 3
start_curr_amount = 0.05
eW = tkgtri.ccxtExchangeWrapper.load_from_id(exchange_id, _keys[exchange_id]["key"],
                                             _keys[exchange_id]["secret"])

eW.get_markets()
balance = eW._ccxt.fetch_balance()
balance_start_curr = balance[start_curr]["free"]

non_zero_balances = {k: v for (k, v) in balance.items() if "free" in v and v["free"] > 0}


symbol = tkgtri.core.get_symbol(start_curr, dest_cur, eW.markets)
side = tkgtri.core.get_order_type(start_curr, dest_cur, symbol)

ob_array = eW._ccxt.fetch_order_book(symbol)
ob = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array['bids'])

d = ob.get_depth_for_destination_currency(start_curr_amount, dest_cur)
price = d.total_price*1
amount = d.total_quantity / d.total_price if side == "sell" else d.total_quantity

order_history_file_name = tkgtri.utils.get_next_filename_index("test_data/orders/{}.json".format(eW.exchange_id))
order_resps = collections.OrderedDict()

order = tkgtri.TradeOrder.create_limit_order_from_start_amount(symbol, start_curr, start_curr_amount, dest_cur, price)

om = tkgtri.OrderManagerFok(order, None, 100, 10)

try:
    om.fill_order(eW)

except OrderManagerErrorUnFilled as e:
    print("Unfilled order. Should cancel and recover/continue")
    try:
        print("Cancelling....")
        om.cancel_order(eW)
    except OrderManagerCancelAttemptsExceeded:
        print("Could not cancel")

except OrderManagerError:
    print("Unknown error")
except Exception as e:
    print(type(e).__name__, "!!!", e.args, ' ')

print("=====================================")
print("Symbol:{}".format(order.symbol))
print("Side:{}".format(order.side))
print("Amount:{}".format(order.amount))
print("Status:{}".format(order.status))
print("Filled dest amount: {} of {}".format(order.filled_dest_amount, order.amount_dest))
print("Filled order amount: {} of {}".format(order.filled, order.amount))
print("Filled src amount: {} of {}".format(order.filled_src_amount, order.amount_start))


sys.exit(0)
# d = ob.(bal_to_bid, dest_cur)
# price = d.total_price
# amount = d.total_quantity


pass
