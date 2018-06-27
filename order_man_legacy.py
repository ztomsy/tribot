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


def tkg_order_fok(order_symbol, start_currency, start_currency_amount, dest_currency, order_price):
    order = tkgtri.TradeOrder.create_limit_order_from_start_amount(order_symbol, start_currency, start_currency_amount, dest_currency,
                                                                   order_price)

    print("Order created")
    print("Symbol:{}".format(order.symbol))
    print("Amount:{}".format(order.amount))

    om = tkgtri.OrderManagerFokLegacyBinance(order, limits, 3)

    try:
        om.run_order_(ccxt_exchange)

    except OrderManagerErrorUnFilled as e:
        print("Unfilled order. Should cancel and recover/continue")

        while order.status != "canceled" and order.status != "closed":
            try:
                om.cancel_order(ccxt_exchange)

            except Exception as e:
                print("Cancel Error")
                print(type(e).__name__, "!!!", e.args, ' ')

            finally:
                resp = om.update_order(ccxt_exchange)
                order.update_order_from_exchange_resp(resp)
                pass

        print("Cancel OK")
        print("Order status: {}".format(order.status))

    except OrderManagerErrorSkip as e:
        print("Not reached minimum amount")

    except OrderManagerError as e:
        print("Unknown error")

    except Exception as e:
        print(type(e).__name__, "!!!", e.args, ' ')


    return order



_keys = {"binance":
             {"key": "O1hGc8oRK7BXfBS7ynXZPcXwjdnaz5fU5RJow9RM7sHCWfMJLgdBAnh6dopCFk5I",
              "secret": "D4ddhpjcerL4F3Hhbwjp5lly1U7UGjVg4N7iyciDf4NwDN85uy262kU3ZeVhQO3X"},
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
start_curr = "BTC"
dest_cur = "ETH"
# start_curr_amount = 0.05 / 3
start_curr_amount = 0.106797

limits = {"BTC": 0.0002, "ETH": 0.02, "BNB": 1, "USDT": 20}

ccxt_exchange = ccxt.binance({"apiKey": _keys["binance"]["key"],
                              "secret": _keys["binance"]["secret"]})

markets = ccxt_exchange.load_markets()

symbol = tkgtri.core.get_symbol(start_curr, dest_cur, markets)
side = tkgtri.core.get_order_type(start_curr, dest_cur, symbol)

ob_array = ccxt_exchange.fetch_order_book(symbol)
ob = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array['bids'])

d = ob.get_depth_for_destination_currency(start_curr_amount, dest_cur)
price = d.total_price*1

o = tkg_order_fok(symbol, start_curr, start_curr_amount, dest_cur, price)

print("=====================================")
print("Symbol:{}".format(o.symbol))
print("Side:{}".format(o.side))
print("Amount:{}".format(o.amount))
print("Status:{}".format(o.status))
print("Filled dest amount: {} of {}".format(o.filled_dest_amount, o.amount_dest))
print("Filled order amount: {} of {}".format(o.amount, o.filled))






