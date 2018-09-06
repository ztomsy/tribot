import tkgtri
import jsonpickle
import sys
import copy
import json

start_currency = "ETH"
dest_currency = "BTC"

start_amount = 0.015
best_dest_amount = 0.36406

# start_currency = "ETH"
# dest_currency = "NEO"
# start_amount = 0.4
# best_dest_amount = 8.4907248

bot = tkgtri.TriBot("../_kucoin.json")
order_history_file_name = tkgtri.utils.get_next_filename_index("./test_order.json")

bot.load_config_from_file(bot.config_filename)

bot.init_exchange()
bot.exchange.set_offline_mode("markets.json", None, "test_order.json")
# bot.load_balance()

bot.load_markets()

if bot.exchange.offline:
    bot.exchange.offline_load_trades_from_file("test_order.json")

#bot.load_tickers()

symbol = tkgtri.core.get_symbol(start_currency, dest_currency, bot.markets)

# balance = bot.exchange.fetch_free_balance()

recovery_order = tkgtri.RecoveryOrder(symbol, start_currency, start_amount, dest_currency, best_dest_amount)

tkgtri.OwaManager.log = bot.log  # override order manager logger to the bot logger
tkgtri.OwaManager.LOG_INFO = bot.LOG_INFO
tkgtri.OwaManager.LOG_ERROR = bot.LOG_ERROR
tkgtri.OwaManager.LOG_DEBUG = bot.LOG_DEBUG
tkgtri.OwaManager.LOG_CRITICAL = bot.LOG_CRITICAL

om = tkgtri.OwaManager(bot.exchange)
om.add_order(recovery_order)

while True:
    if len(om.get_open_orders()) > 0:
        om.proceed_orders()
    else:
        bot.log(bot.LOG_INFO, "No more open orders")
        break

bot.log(bot.LOG_INFO, "Finished")