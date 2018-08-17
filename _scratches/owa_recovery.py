import tkgtri
import jsonpickle
import sys
import copy
import json

start_currency = "NEO"
dest_currency = "ETH"

start_amount = 9.7812825
best_dest_amount = 9.7812825*0.0592861

# start_currency = "ETH"
# dest_currency = "NEO"
# start_amount = 0.4
# best_dest_amount = 8.4907248

bot = tkgtri.TriBot("../_kucoin.json")
order_history_file_name = tkgtri.utils.get_next_filename_index("./test_order.json")

bot.load_config_from_file(bot.config_filename)

bot.init_exchange()
# bot.exchange.set_offline_mode("markets.json", None, "test_order.json")
# bot.load_balance()

bot.load_markets()

if bot.exchange.offline:
    bot.exchange.offline_load_trades_from_file("test_order.json")

#bot.load_tickers()

symbol = tkgtri.core.get_symbol(start_currency, dest_currency, bot.markets)

# balance = bot.exchange.fetch_free_balance()

recovery_order = tkgtri.RecoveryOrder(symbol, start_currency, start_amount, dest_currency, best_dest_amount)

best_price = recovery_order.get_recovery_price_for_best_dest_amount()

om = tkgtri.OwaManager(bot.exchange)
om.add_order(recovery_order)

while True:
    om.proceed_orders()
    pass









