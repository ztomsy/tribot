import tkgtri
import jsonpickle
import sys
import copy
import json

start_currency = "ETH"
dest_currency = "TEL"

start_amount = 0.2

bot = tkgtri.TriBot("../_kucoin.json")
order_history_file_name = tkgtri.utils.get_next_filename_index("./test_order.json")
markets_file_name = tkgtri.utils.get_next_filename_index("./markets.json")

bot.load_config_from_file(bot.config_filename)

bot.init_exchange()
bot.load_markets()

symbol = tkgtri.core.get_symbol(start_currency, dest_currency, bot.markets)

balance = bot.exchange.fetch_free_balance()

ob_array = bot.exchange._ccxt.fetch_order_book(symbol, 100)
order_book = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array["bids"])

init_price = order_book.get_depth_for_destination_currency(start_amount, dest_currency).total_price
bot.log(bot.LOG_INFO, "Price:{}".format(init_price))

order = tkgtri.TradeOrder.create_limit_order_from_start_amount(symbol, start_currency, start_amount, dest_currency,
                                                               init_price )

order_history = dict()
order_history["updates"] = list()


def on_order_create(self: tkgtri.OrderManagerFok):
    bot.log(bot.LOG_INFO, "Order {} created. Filled dest curr:{} / {} ".format(self.order.id, self.order.filled_dest_amount,
                                                               self.order.amount_dest))
    order_history["create"] = copy.copy(self.order)


def on_order_update(self: tkgtri.OrderManagerFok):
    bot.log(bot.LOG_INFO, "Order {} updated. Filled dest curr:{} / {} ".format(self.order.id, self.order.filled_dest_amount,
                                                               self.order.amount_dest))
    order_history["updates"].append(copy.copy(self.order))


tkgtri.OrderManagerFok.on_order_create = on_order_create
tkgtri.OrderManagerFok.on_order_update = on_order_update
om = tkgtri.OrderManagerFok(order)

try:
    om.fill_order(bot.exchange)

except tkgtri.OrderManagerErrorUnFilled:
    print("Cancelling Order")
    om.cancel_order(bot.exchange)

resp_trades = bot.get_trade_results(order)
order.update_order_from_exchange_resp(resp_trades)
order_history["updates"].append(copy.copy(order))
order_history["trades"] = order.trades

bot.log(bot.LOG_INFO, "Saving to file: {}".format(order_history_file_name))

j = jsonpickle.encode(order_history, unpicklable= False)
s = json.dumps(json.loads(j), indent=4, sort_keys=True)

with open(order_history_file_name, "w") as file:
    file.writelines(s)

bot.log(bot.LOG_INFO, "Saving markets to file {}...".format(markets_file_name))
j = jsonpickle.encode(bot.markets, unpicklable= False)
s = json.dumps(json.loads(j), indent=4, sort_keys=True)

with open(markets_file_name, "w") as file:
    file.writelines(s)



#
# # # #
# # # #
#






sys.exit()
pass
#order = tkgtri.RecoveryOrder("ETH/BTC", )