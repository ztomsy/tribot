from tkgtri import TriBot
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
# ---------------------------------------

tribot.log(tribot.LOG_INFO, "Started")

tribot.set_from_cli(sys.argv[1:])  # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename)  # config taken from cli or default

tribot.init_timer()
tribot.timer.notch("start")


tribot.log(tribot.LOG_INFO, "Exchange ID:" + tribot.exchange_id)
tribot.log(tribot.LOG_INFO, "Debug: {}".format(tribot.debug))


# now we have exchange_id from config file or cli
tribot.init_reports("_"+tribot.exchange_id+"/")

try:
    tribot.init_exchange()
    tribot.load_markets()


except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error while exchange initialization {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    sys.exit(0)

if len(tribot.markets) < 1:
    tribot.log(tribot.LOG_ERROR, "Zero markets {}".format(tribot.exchange_id))
    sys.exit(0)

try:
    tribot.set_triangles()
except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error while preparing triangles {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    sys.exit(0)

if tribot.basic_triangles_count < 1:
    tribot.log(tribot.LOG_ERROR, "Zero basic triangles".format(tribot.exchange_id))
    sys.exit(0)

tribot.log(tribot.LOG_INFO, "Basic Triangles found: {}".format(tribot.basic_triangles_count))

while True:

    tribot.load_balance()
    tribot.log(tribot.LOG_INFO, "Balance: {}".format(tribot.balance))

    while True:

        try:
            tribot.timer.check_timer()
            tribot.fetch_tickers()
            print("Tickers fetched {}".format(len(tribot.tickers)))

        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error while fetching tickers {}".format(tribot.exchange_id))
            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
            sys.exit()

        continue

    continue

tribot.log(tribot.LOG_INFO, "Total time:" + str((tribot.timer.notches[-1]["time"] - tribot.timer.start_time).total_seconds()))
tribot.log(tribot.LOG_INFO, "Finished")







