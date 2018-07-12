import tkgtri
import sys
import json
import collections

from tkgtri.trade_manager import *

_keys = {"binance":
             {"key": "M1lHFjmqzixs1S8IqST9lXP2DvzJuqNTR4lgpuv1PmutDTwxIAXRdjayTTVOR3SX",
              "secret": "Scov95f2UtBmtDb8J8PsWGXxVohNzWGC50CebPkriRHV1M6S6KVqYforOLNRYYXE"}
         }


exchange_id = "binance"
start_curr = "BTC"
dest_cur = "ETH"
# start_curr_amount = 0.05 / 3
start_curr_amount = 0.01
eW = tkgtri.ccxtExchangeWrapper.load_from_id(exchange_id, _keys[exchange_id]["key"],
                                             _keys[exchange_id]["secret"])

eW.get_markets()

order_data = eW._ccxt.fetch_order('16018976', "HSR/ETH")

order = TradeOrder(order_data["type"], order_data["symbol"], order_data["amount"], order_data["side"])

order.update_order_from_exchange_resp(order_data)

trades = eW._ccxt.fetch_my_trades(order.symbol, order.timestamp)

trades_result = order.total_amounts_from_trades(trades)

precise_amount = eW._ccxt.amount_to_precision(order.symbol, trades_result["amount"])
precise_cost = eW._ccxt.cost_to_precision(order.symbol, trades_result["cost"])
precise_price = eW._ccxt.price_to_precision(order.symbol, trades_result["price"])



sys.exit()


balance = eW._ccxt.fetch_balance()
balance_start_curr = balance[start_curr]["free"]

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
