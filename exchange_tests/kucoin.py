import tkgtri
import sys
import json
import collections
import jsonpickle
from jsonpickle import handlers
import tkgtri
from tkgtri import tribot
from tkgtri.orderbook import OrderBook
from tkgtri.trade_manager import *
import  ccxt

exchange_id = "kucoin"
start_cur = "BTC"
dest_cur = "ETH"

bot = tkgtri.TriBot("../_kucoin.json", "kucoin_test.log")
bot.load_config_from_file(bot.config_filename)

if start_cur != bot.start_currency[0]:
    print("Start currency in config != start currency in test {} != {}".format(bot.start_currency[0], start_cur))
    sys.exit(0)

bot.init_logging(bot.log_filename)
bot.init_exchange()
bot.load_markets()
bot.load_balance()
bot.fetch_tickers()


order_history_file_name = tkgtri.utils.get_next_filename_index("./{}_all_objects.json".format(bot.exchange_id))

def test_trade(start_cur, dest_cur, start_amount):

    balance = dict()
    while not balance:
        try:
            balance = bot.exchange.fetch_free_balance()
        except:
            print("Retry fetching balance...")

    init_balance = dict()
    init_balance[start_cur] = balance[start_cur]
    init_balance[dest_cur] = balance[dest_cur]

    symbol = tkgtri.core.get_symbol(start_cur, dest_cur, bot.markets)
    ob_array = dict()
    while not ob_array:
        try:
            ob_array = bot.exchange._ccxt.fetch_order_book(symbol, 100)
        except:
            print("retying to fetch order book")

    order_book = OrderBook(symbol, ob_array["asks"], ob_array["bids"])

    price = order_book.get_depth_for_destination_currency(start_amount, dest_cur).total_price

    order1 = tkgtri.TradeOrder.create_limit_order_from_start_amount(symbol, start_cur, start_amount, dest_cur, price)

    order_resps = collections.OrderedDict()

    om = tkgtri.OrderManagerFok(order1, None, 100, 10)

    try:
        om.fill_order(bot.exchange)
    except OrderManagerErrorUnFilled as e:
        print("Unfilled order. Should cancel and recover/continue")
        try:
            print("Cancelling....")
            om.cancel_order(bot.exchange)
        except OrderManagerCancelAttemptsExceeded:
            print("Could not cancel")

    except OrderManagerError as e:
        print("Unknown  Order Manager error")
        print(type(e).__name__, "!!!", e.args, ' ')

    except ccxt.errors.InsufficientFunds:
        print("Low balance!")
        sys.exit(0)

    except Exception as e:
        print("error")
        print(type(e).__name__, "!!!", e.args, ' ')
        sys.exit(0)

    results = list()
    i = 0
    while bool(results) is not True and i < 100:
        print("retrying to get trades #{}".format(i))
        try:
            results = bot.exchange.get_trades_results(order1)
        except:
            print("retrying to get trades...")
        i += 1

    order1.trades = results
    order1.fees = bot.exchange.get_total_fees(order1)

    balance_after_order1 = dict(init_balance)

    i = 0
    while balance_after_order1[start_cur] == init_balance[start_cur] and i < 50:
        try:
            balance = dict(bot.exchange.fetch_free_balance())
            balance_after_order1[start_cur], balance_after_order1[dest_cur] = balance[start_cur], balance[dest_cur]
        except:
            print("Error receiving balance")

        print("Balance receive attempt {}".format(i))
        i += 1

    all_data = dict()

    all_data["exchange_id"] = bot.exchange_id
    all_data["start_balance"] = init_balance
    all_data["balance_after_order1"] = balance_after_order1
    all_data["start_currency"] = start_cur
    all_data["dest_currency"] = dest_cur
    all_data["symbol"] = symbol
    all_data["price"] = price
    all_data["order1"] = order1
    all_data["order_book_1"] = order_book
    all_data["market"] = bot.markets[symbol]
    all_data["ticker"] = bot.tickers[symbol]
    all_data["balance_after_order1"] = balance_after_order1
    all_data["balance_diff_start_cur"] = init_balance[start_cur] - balance_after_order1[start_cur]
    all_data["balance_diff_dest_cur"] = init_balance[dest_cur] - balance_after_order1[dest_cur]
    all_data["check_balance_dest_curr_diff_eq_filled_dest_minus_fee"] = True \
        if balance_after_order1[dest_cur] == init_balance[dest_cur] + \
           order1.filled_dest_amount - order1.fees[dest_cur]["amount"] else False

    all_data["check_balance_src_curr_diff_eq_filled_src"] = True \
        if balance_after_order1[start_cur] == init_balance[start_cur] - order1.filled_src_amount else False

    return all_data


report = dict()

report["trade1"] = test_trade(start_cur, dest_cur, bot.min_amounts[start_cur])

j = jsonpickle.encode(report)

s = json.dumps(json.loads(j), indent=4)

with open(order_history_file_name, "w") as file:
    file.writelines(s)

print("Order resp:")
print(s)
print("Trades resp:{}".format(results))

print("=====================================")
print("Symbol:{}".format(order1.symbol))
print("Side:{}".format(order1.side))
print("Amount:{}".format(order1.amount))
print("Price:{}".format(order1.init_price))
print("Status:{}".format(order1.status))
print(" - - - -")
print("Result:")
print("Filled order amount: {} of {}".format(order1.filled, order1.amount))
print("Filled dest amount: {} of {}".format(results["dest_amount"], order1.filled_dest_amount))
print("Filled src amount: {} of {}".format(results["src_amount"], order1.amount_start))
print("Price Fact vs Order price  : {} of {}".format(results["price"], order1.init_price))
print("Trades count: {}".format(len(results["trades"])))

sys.exit(0)
# d = ob.(bal_to_bid, dest_cur)
# price = d.total_price
# amount = d.total_quantity
