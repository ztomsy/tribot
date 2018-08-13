import tkgtri
import jsonpickle
import sys
import copy
import json

start_currency = "ETH"
dest_currency = "TEL"

start_amount = 0.2
best_dest_amount = 100000

bot = tkgtri.TriBot("../_kucoin.json")
order_history_file_name = tkgtri.utils.get_next_filename_index("./test_order.json")

bot.load_config_from_file(bot.config_filename)

bot.init_exchange()
bot.load_markets()
bot.exchange.set_offline_mode("markets.json", None, "test_order.json")
bot.exchange.offline_load_trades_from_file("test_order.json")

symbol = tkgtri.core.get_symbol(start_currency, dest_currency, bot.markets)

balance = bot.exchange.fetch_free_balance()

recovery_order = tkgtri.RecoveryOrder(symbol, start_currency, start_amount, dest_currency, best_dest_amount)

best_price = recovery_order.get_recovery_price_for_best_dest_amount()

order = recovery_order.create_recovery_order(recovery_order.get_recovery_price_for_best_dest_amount())

om = tkgtri.OrderManagerFok(order)

try:
    om.fill_order(bot.exchange)

except tkgtri.OrderManagerErrorUnFilled:
    print("Cancelling Order")
    om.cancel_order(bot.exchange)




