from tkgtri import TriBot
import sys
import traceback

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
tribot.log(tribot.LOG_INFO, "session_uuid:" + tribot.session_uuid)
tribot.log(tribot.LOG_INFO, "Debug: {}".format(tribot.debug))

# now we have exchange_id from config file or cli
tribot.init_reports("_"+tribot.exchange_id+"/")
tribot.init_remote_reports()

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

if len(tribot.all_triangles) < 1:
    tribot.log(tribot.LOG_ERROR, "Zero basic triangles".format(tribot.exchange_id))
    sys.exit(0)

tribot.log(tribot.LOG_INFO, "Triangles found: {}".format(len(tribot.all_triangles)))

while True:

    tribot.load_balance()
    tribot.log(tribot.LOG_INFO, "Balance: {}".format(tribot.balance))

    while True:
        tribot.timer.reset_notches()

        # exit when debugging and because of errors
        if tribot.debug is True and tribot.errors > 0:
            tribot.log(tribot.LOG_INFO, "Exit on errors, debugging")
            sys.exit(666)

        # resetting error
        tribot.errors = 0

        # fetching tickers
        try:
            tribot.timer.check_timer()
            tribot.timer.notch("time_from_start")
            tribot.fetch_tickers()
            tribot.timer.notch("duration_fetch")
            print("Tickers fetched {}".format(len(tribot.tickers)))
        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error while fetching tickers exchange_id:{} session_uuid:{} fetch_num:{} :".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number))

            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

            tribot.errors += 1

        # proceeding tickers
        try:
            tribot.proceed_triangles()
            tribot.get_good_triangles()

            tribot.reporter.set_indicator("good_triangles", len(tribot.tri_list_good))
            tribot.reporter.set_indicator("total_triangles", len(tribot.tri_list))

            tribot.reporter.set_indicator("best_triangle", tribot.tri_list[0]["triangle"])
            tribot.reporter.set_indicator("best_result", tribot.tri_list[0]["result"])

            tribot.timer.notch("duration_proceed")

        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Error while proceeding tickers exchange_id{}: session_uuid:{} fetch_num:{} :".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number))

            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)

            tribot.errors += 1

        # reporting states:
        tribot.reporter.set_indicator("session_uuid", tribot.session_uuid)
        tribot.reporter.set_indicator("fetch_number", tribot.fetch_number)
        tribot.reporter.set_indicator("errors", tribot.errors)

        tribot.reporter.push_to_influx()
        tribot.timer.notch("duration_to_influx")

        print("Fetch_num: {}".format(tribot.fetch_number))
        print("Errors: {}".format(tribot.errors))
        print("Good triangles: {} / {} ".format(len(tribot.tri_list_good),
                                                len(tribot.tri_list)))
        print("Best triangle {}: {} ".format(tribot.last_proceed_report["best_result"]["triangle"],
                                             tribot.last_proceed_report["best_result"]["result"]))
        print("Tickers proceeded {} time".format(len(tribot.tickers)))
        print("Duration,s: " + str(tribot.timer.results_dict()))
        print("====================================================================================")


tribot.log(tribot.LOG_INFO, "Total time:" + str((tribot.timer.notches[-1]["time"] - tribot.timer.start_time).total_seconds()))
tribot.log(tribot.LOG_INFO, "Finished")







