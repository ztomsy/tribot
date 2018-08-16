#
# utility to test order manager for legacy script
#
#

import tkgtri
import sys
import json
import collections
import ccxt
from tkgtri import OrderManagerError, OrderManagerErrorUnFilled, OrderManagerErrorSkip
from tkgtri.trade_manager import *


def tkg_order_fok(exchange, max_order_update_requests, max_cancel_attempts, trade_limits, order_symbol, order_amount,
                  order_side, order_price):
    order = tkgtri.TradeOrder("limit", order_symbol, order_amount, order_side, order_price)

    print("Order created")
    print("Symbol:{}".format(order.symbol))
    print("Amount:{}".format(order.amount))

    om = tkgtri.OrderManagerFokLegacyBinance(order, trade_limits, max_order_update_requests, max_cancel_attempts)

    try:
        om.fill_order(exchange)

    except OrderManagerErrorUnFilled as e:
        print("Unfilled order. Should cancel and recover/continue")
        try:
            print("Cancelling....")
            om.cancel_order(exchange)
        except OrderManagerCancelAttemptsExceeded:
            print("Could not cancel")

    except OrderManagerError:
        print("Unknown error")
    except Exception as e:
        print(type(e).__name__, "!!!", e.args, ' ')
    return order


_keys = {"binance":
             {"key": "M1lHFjmqzixs1S8IqST9lXP2DvzJuqNTR4lgpuv1PmutDTwxIAXRdjayTTVOR3SX",
              "secret": "Scov95f2UtBmtDb8J8PsWGXxVohNzWGC50CebPkriRHV1M6S6KVqYforOLNRYYXE"},
         "kucoin":
             {"key": "5b22b10709e5a14f2c125e3d",
              "secret": "11ec0073-8919-4863-a518-7e2468506752"}
         }

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("binance",
#                                              "AmEkXUlAh3fW1XkxIOSLovMVia1B55bWI2937Y9ZGRu25uJj2XSCBbOGoI8bb8II",
#                                              "6yy8vrkUR3aOBJyUkzRtEHGYR01gxMmyYJ6jMHyt3HxY7AtXlKr54FmtPOLUsBvh")

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin",
#                                              "5b22b10709e5a14f2c125e3d", "11ec0073-8919-4863-a518-7e2468506752")

exchange_id = "binance"
start_curr = "DENT"
dest_cur = "ETH"
# start_curr_amount = 0.05 / 3
start_curr_amount = 57181

limits = {"BTC": 0.0002, "ETH": 0.02, "BNB": 1, "USDT": 20}

ccxt_exchange = ccxt.binance({"apiKey": _keys["binance"]["key"],
                              "secret": _keys["binance"]["secret"]})

markets = ccxt_exchange.load_markets()

balances = ccxt_exchange.fetch_balance()

non_zero_balances = {k: v for (k, v) in balances.items() if "free" in v and v["free"] > 0}
print(non_zero_balances)

symbol = tkgtri.core.get_symbol(start_curr, dest_cur, markets)
side = tkgtri.core.get_order_type(start_curr, dest_cur, symbol)

ob_array = ccxt_exchange.fetch_order_book(symbol)
ob = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array['bids'])

d = ob.get_depth_for_destination_currency(start_curr_amount, dest_cur)
price = d.total_price * 1.005

o_temp = tkgtri.TradeOrder.create_limit_order_from_start_amount(symbol, start_curr, start_curr_amount, dest_cur, price)

o = tkg_order_fok(ccxt_exchange, 100, 10, limits, o_temp.symbol, o_temp.amount, o_temp.side, price)

print("=====================================")
print("Symbol:{}".format(o.symbol))
print("Side:{}".format(o.side))
print("Amount:{}".format(o.amount))
print("Status:{}".format(o.status))
print("Filled dest amount: {} of {}".format(o.filled_dest_amount, o.amount_dest))
print("Filled order amount: {} of {}".format(o.filled, o.amount))
print("Filled src amount: {} of {}".format(o.filled_start_amount, o.amount_start))
