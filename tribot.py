from tkgtri import *
import ccxt
import sys

TriBot.print_logo("TriBot v0.5")

#
# set default parameters
#
tribot = TriBot("_config_default.json", "_tri.log")

tribot.report_all_deals_filename = "%s/_all_deals.csv"  # full path will be exchange_id/all_deals.csv
tribot.report_tickers_filename = "%s/all_tickers_%s.csv"
tribot.report_deals_filename = "%s/deals_%s.csv"
tribot.report_prev_tickers_filename = "%s/deals_%s_tickers.csv"

tribot.test_balance = 1
tribot.debug = True
tribot.live = True

tribot.set_log_level(tribot.LOG_INFO)
#---------------------------------------

timer = Timer()
timer.notch("start")

tribot.log(tribot.LOG_INFO, "Started")

tribot.set_from_cli(sys.argv[1:])  # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename)  # config taken from cli or default

tribot.log(tribot.LOG_INFO, "Exchange ID:" + tribot.exchange_id)

# now we have exchange_id from config file or cli
tribot.init_reports("_"+tribot.exchange_id+"/")

try:
    tribot.init_exchange()

except Exception as e:

    tribot.log(tribot.LOG_ERROR, "Error while exchange initialization {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)


tribot.log(tribot.LOG_CRITICAL, "Finished")
timer.notch("finished")

tribot.log(tribot.LOG_INFO, "Total time:" + str((timer.notches[-1]["time"] - timer.start_time).total_seconds()))

tribot.log(tribot.LOG_INFO, "Finished")







