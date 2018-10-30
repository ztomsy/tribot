from tkgtri import TriBot
from tkgtri import tri_arb as ta
import uuid
import sys
import traceback
import time

TriBot.print_logo("TriBot v0.5")

#
# set default parameters
#
tribot = TriBot("_config.json", "_tri.log")

tribot.report_all_deals_filename = "%s/_all_deals.csv"  # full path will be exchange_id/all_deals.csv
tribot.report_tickers_filename = "%s/all_tickers_%s.csv"
tribot.report_deals_filename = "%s/deals_%s.csv"
tribot.report_prev_tickers_filename = "%s/deals_%s_tickers.csv"

tribot.debug = False
tribot.force_best_tri = True

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
tribot.log(tribot.LOG_INFO, "Force trades with best result: {}".format(tribot.force_best_tri))
tribot.log(tribot.LOG_INFO, "Offline mode: {}".format(tribot.offline))
tribot.log(tribot.LOG_INFO, "Start currency: {}".format(tribot.start_currency[0]))
tribot.log(tribot.LOG_INFO, "Sleep time on fetching tickers error: {}".format(tribot.sleep_on_tickers_error))

# now we have exchange_id from config file or cli
tribot.init_reports("_"+tribot.exchange_id+"/")

# init the remote reporting
try:
    tribot.init_remote_reports()
except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error Report DB connection {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    tribot.log(tribot.LOG_INFO, "Continue....", e.args)
try:

    tribot.init_exchange()
    if tribot.offline:
        tribot.log(tribot.LOG_INFO, "Loading from offline test_data/markets.json test_data/tickers.csv")
        tribot.exchange.set_offline_mode("test_data/markets.json", "test_data/tickers.csv")
    else:
        tribot.exchange.init_async_exchange()

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


# fetching the balance for first start currency or taking test balance from the cli/config
try:
    tribot.load_balance()
    tribot.log(tribot.LOG_INFO, "Init Balance: {}".format(tribot.balance))

except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error while fetching balance {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    tribot.log(tribot.LOG_ERROR, "Exiting")
    sys.exit("666")

# main loop
while True:

    # reporting from previous iteration
    if tribot.fetch_number > 0 and working_triangle is not None:
        print("Previous results")
        # additional reporting collection

        tribot.timer.notch("time_after_deals")

        report = tribot.get_deal_report(working_triangle, recovery_data, order1, order2, order3, price1, price2,
                                        price3)
        # we are not reporting and reloading balance if OB STOP
        if "status" in working_triangle and working_triangle["status"] != "OB STOP":

            tribot.log(tribot.LOG_INFO, "====================================")
            tribot.log(tribot.LOG_INFO, "============ DEAL REPORT ===========")
            tribot.log_report(report)
            tribot.log(tribot.LOG_INFO, "====================================")
            tribot.log(tribot.LOG_INFO, "Saving to file...")
            tribot.save_single_deal_csv(report)

            try:
                tribot.send_remote_report(report)
                tribot.timer.notch("time_to_send_report")
            except Exception as e:
                tribot.log(tribot.LOG_ERROR, "Error sending report")
                tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
                tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

            # saving order books
            try:
                tribot.log(tribot.LOG_INFO, "Saving order books")
                tribot.save_order_books(report["deal-uuid"], order_books)
            except:
                tribot.log(tribot.LOG_ERROR, "Could not save Order books")

        # reload balance if it was a deal (noty OB STOP or error)
        if "status" in working_triangle and \
                working_triangle["status"] not in ("OB STOP", "ERROR"):
            tribot.reload_balance(report["result-fact-diff"])



    if tribot.fetch_number > 0 and tribot.run_once:
        tribot.log(tribot.LOG_INFO, "Exiting because of Run once")
        sys.exit(666)

    # reset timer
    tribot.timer.reset_notches()

    # init working variables
    working_triangle = None
    order_books = dict()
    expected_result = 0.0
    bal_to_bid = 0.0
    recovery_data = list()  # list of recovery data dict
    report = dict()
    order1, order2, order3 = (None, None, None)
    price1, price2, price3 = (None, None, None)

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
        tribot.timer.notch("time_fetch")
        print("Tickers fetched {}".format(len(tribot.tickers)))
    except Exception as e:
        tribot.log(tribot.LOG_ERROR, "Error while fetching tickers exchange_id:{} session_uuid:{} fetch_num:{} :".
                   format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number))

        tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
        tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
        tribot.log(tribot.LOG_INFO, "Sleeping for {}s".format(tribot.sleep_on_tickers_error))
        time.sleep(tribot.sleep_on_tickers_error)
        tribot.errors += 1
        continue  # drop the trades and return to ticker fetch loop

    # proceeding tickers
    try:
        tribot.proceed_triangles()
        tribot.tri_list_good = tribot.get_good_triangles()  # tri_list became sorted after this

        tribot.reporter.set_indicator("good_triangles", len(tribot.tri_list_good))
        tribot.reporter.set_indicator("total_triangles", len(tribot.tri_list))
        tribot.reporter.set_indicator("best_triangle", tribot.tri_list[0]["triangle"])
        tribot.reporter.set_indicator("best_result", tribot.tri_list[0]["result"])

        tribot.timer.notch("time_proceed")

    except Exception as e:
        tribot.log(tribot.LOG_ERROR, "Error while proceeding tickers exchange_id{}: session_uuid:{} fetch_num:{} :".
                   format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number))

        tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
        tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)

        tribot.errors += 1
        continue

    # checking the good triangles and live flag
    if not tribot.force_best_tri and len(tribot.tri_list_good) <= 0:
        continue  # no good triangles

    # check the Order Book result for min amount
    if tribot.force_best_tri:
        working_triangle = tribot.tri_list[0]  # taking best triangle

    else:  # taking the best triangle and max balance to bid
        working_triangle = tribot.tri_list_good[0]  # taking best good triangle

    # Try to go into deal
    tribot.log(tribot.LOG_INFO, "============================================================")
    tribot.log(tribot.LOG_INFO, "Good result: {} for {}".format(working_triangle["result"],
                                                                working_triangle["triangle"]))

    # set the best status for the best!
    working_triangle["status"] = "OK"

    # create deal_uuid
    working_triangle["deal-uuid"] = str(uuid.uuid4())
    tribot.log(tribot.LOG_INFO, "Deal-uuid: {}".format(working_triangle["deal-uuid"]))

    # fetching the order books for symbols in triangle if the check_order_books option is activated
    if tribot.check_order_books:
        try:
            tribot.log(tribot.LOG_INFO, "Try to fetch order books: {} {} {} ".format(working_triangle["symbol1"],
                                                                                     working_triangle["symbol2"],
                                                                                     working_triangle["symbol3"]))
            tribot.timer.notch("time_get_order_books")
            order_books = tribot.get_order_books_async(list([working_triangle["symbol1"],
                                                             working_triangle["symbol2"],
                                                             working_triangle["symbol3"]]))
            tribot.log(tribot.LOG_INFO, "Order books fetched")
        except Exception as e:
            working_triangle["status"] = "ERROR"

            tribot.log(tribot.LOG_ERROR, "Error while fetching order books exchange_id:{} session_uuid:{}"
                                         " fetch_num:{}:"
                                         " for {}{}{}".
                       format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number, working_triangle["symbol1"],
                              working_triangle["symbol2"],working_triangle["symbol3"]))
            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
            tribot.errors += 1
            continue

        # check Order Book result for min amount
        try:
            tribot.log(tribot.LOG_INFO, "Checking OB Result for min amount:{}"
                       .format(tribot.min_amounts[tribot.start_currency[0]]))

            expected_result = ta.order_book_results(tribot.exchange, working_triangle,
                                                          {1: order_books[working_triangle["symbol1"]],
                                                           2: order_books[working_triangle["symbol2"]],
                                                           3: order_books[working_triangle["symbol3"]]},
                                                    tribot.min_amounts[tribot.start_currency[0]])["result"]
        except Exception as e:
            tribot.log(tribot.LOG_ERROR,
                       "Error calc the result and amount on order books for MIN Amount exchange_id{}: session_uuid:{}"
                       " fetch_num:{} :""for {}{}{}".format(tribot.exchange_id, tribot.session_uuid,
                                                            tribot.fetch_number, working_triangle["symbol1"],
                                                            working_triangle["symbol2"],
                                                            working_triangle["symbol3"]))
            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

            working_triangle["status"] = "ERROR"
            tribot.errors += 1
            continue

        working_triangle["ob_result"] = expected_result * ((1-tribot.commission)**3)
        tribot.log(tribot.LOG_INFO, "...order book result w commission for min amount {}: {}".format(
            tribot.min_amounts[tribot.start_currency[0]],working_triangle["ob_result"]))

        # checking OB STOP
        if working_triangle["ob_result"] < tribot.threshold_order_book and\
                (not tribot.force_start_amount and not tribot.force_best_tri):
            working_triangle["status"] = "OB STOP"
            tribot.log(tribot.LOG_INFO, "OB STOP")
            tribot.log(tribot.LOG_INFO, "Order book result: {}".format(working_triangle["ob_result"]))
            continue

    # getting max amount to bid from balance and bot's parameters

    bal_to_bid = tribot.start_amount_to_bid(working_triangle, order_books, tribot.force_best_tri,
                                            tribot.force_start_amount)

    # getting max amount to bid from order book if the option "check_order_books" is activated requested
    if tribot.check_order_books:

        try:
            expected_result, ob_result, bid_from_order_book =\
                tribot.restrict_amount_to_bid_from_order_book(bal_to_bid, working_triangle, order_books,
                                                              tribot.force_start_amount)
            working_triangle["ob_result"] = ob_result
        except Exception as e:
            working_triangle["status"] = "ERROR"
            tribot.log(tribot.LOG_ERROR, "Error. Start amount from order books exchange_id{}:"
                                         " session_uuid:{} fetch_num:{} :for {}{}{}"
                       .format(tribot.exchange_id, tribot.session_uuid, tribot.fetch_number,
                               working_triangle["symbol1"], working_triangle["symbol2"],
                               working_triangle["symbol3"]))
            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
            tribot.errors += 1
            continue

        # apply results from tickers prices if  needed
        if tribot.force_start_amount > bid_from_order_book and tribot.prices_from_ticker:

            tribot.log(tribot.LOG_INFO, "Force start amount greater than from OB {} > {} ".format(
                tribot.force_start_amount, bid_from_order_book))
            tribot.log(tribot.LOG_INFO, "... going with ticker prices")

            bal_to_bid = tribot.force_start_amount
            expected_result = working_triangle["result"]
            working_triangle["ob_result"] = working_triangle["result"]


    # double check if initial bid is not None and float
    if bal_to_bid is None or not isinstance(bal_to_bid, float):
        tribot.log(tribot.LOG_ERROR, "Initial balance is None and/or not float {}".format(bal_to_bid))
        tribot.errors += 1
        continue

    # going to deals
    tribot.log(tribot.LOG_INFO, "Amount to Bid: {}".format(bal_to_bid))
    expected_amount = tribot.exchange.price_to_precision(working_triangle["symbol3"],
                                                         bal_to_bid * expected_result)

    tribot.log(tribot.LOG_INFO, "Start amount:{}".format(bal_to_bid))
    tribot.log(tribot.LOG_INFO, "Expected amount w/o commission: {}".format(expected_amount))
    tribot.log(tribot.LOG_INFO, "Expected result w/o commission: {}".format(expected_result))
    tribot.log(tribot.LOG_INFO, "Commission: {}".format(tribot.commission))

    tribot.assign_updates_functions_for_order_manager()

    orders = list()
    working_triangle["status"] = "OK"

    # Order 1
    price1 = tribot.exchange.price_to_precision(working_triangle["symbol1"],
                                                order_books[working_triangle["symbol1"]].get_depth_for_trade_side(
                                                   bal_to_bid, working_triangle["leg1-order"]).total_price)

    tribot.log(tribot.LOG_INFO, "Trade 1/3: from {}-{}->{}".format(working_triangle["cur1"],
                                                                   working_triangle["leg1-order"],
                                                                   working_triangle["cur2"]))

    tribot.log(tribot.LOG_INFO, "Price: {}. Src Amount {}".format(price1, bal_to_bid))

    order1 = tribot.do_trade(working_triangle["symbol1"], working_triangle["cur1"], working_triangle["cur2"],
                             bal_to_bid, working_triangle["leg1-order"], price1)

    if order1.filled_dest_amount > 0:
        resp_trades = tribot.get_trade_results(order1)
        order1.update_order_from_exchange_resp(resp_trades)
        order1.fees = tribot.exchange.fees_from_order(order1)

        if order1.filled < order1.amount * 0.99999:
            tribot.log(tribot.LOG_INFO, "Order 1 Partial Fill.")
            working_triangle["leg1-order-result"] = "PartFill"

    else:
        working_triangle["leg1-order-result"] = "Failed"
        working_triangle["status"] = "Failed 1"
        tribot.log(tribot.LOG_ERROR, "Order1 have not filled at all. Skipping")
        continue

    tribot.log(tribot.LOG_INFO, "Order1: filled {} with fee {}".format(
        order1.filled_dest_amount, order1.fees[order1.dest_currency]["amount"]))

    # Order 2
    order2_amount = order1.filled_dest_amount - order1.fees[order1.dest_currency]["amount"]

    price2 = tribot.exchange.price_to_precision(working_triangle["symbol2"],
                                               order_books[working_triangle["symbol2"]].get_depth_for_trade_side(
                                                   order2_amount,
                                                   working_triangle["leg2-order"]).total_price)

    tribot.log(tribot.LOG_INFO, "Trade 2/3: from {}-{}->{}".format(working_triangle["cur2"],
                                                                   working_triangle["leg2-order"],
                                                                   working_triangle["cur3"]))

    tribot.log(tribot.LOG_INFO, "Price: {}. Src amount {}".format(price2, order2_amount))

    order2 = tribot.do_trade(working_triangle["symbol2"], working_triangle["cur2"], working_triangle["cur3"],
                             order2_amount, working_triangle["leg2-order"], price2)

    if order2.filled_dest_amount > 0:
        resp_trades = tribot.get_trade_results(order2)
        order2.update_order_from_exchange_resp(resp_trades)
        order2.fees = tribot.exchange.fees_from_order(order2)

        working_triangle["leg2-price-fact"] = order2.filled / order2.cost
        working_triangle["leg2-order-status"] = order2.status

        if order2.filled < order2.amount * 0.9999:
            tribot.log(tribot.LOG_INFO, "Order 2 Partial Fill.")
            working_triangle["leg2-order-result"] = "PartFill"
            working_triangle["leg2-recover-amount"] = order2.amount_start - order2.filled_start_amount
            working_triangle["leg2-recover-start-curr-best-amount"] = tribot.order2_best_recovery_start_amount(
                order1.filled_start_amount, order2.amount, order2.filled)

            order_rec_data = tribot.create_recovery_data(working_triangle["deal-uuid"], working_triangle["cur2"],
                                                         working_triangle["cur1"],
                                                         working_triangle["leg2-recover-amount"],
                                                         working_triangle["leg2-recover-start-curr-best-amount"], 2)

            recovery_data.append(order_rec_data)
            tribot.print_recovery_data(order_rec_data)
            tribot.send_recovery_request(order_rec_data)
        else:
            working_triangle["leg2-order-result"] = "Filled"

    else:
        # recover from order2
        working_triangle["leg2-order-result"] = "Failed"
        working_triangle["leg2-recover-amount"] = order2.amount_start
        working_triangle["leg2-recover-start-curr-best-amount"] = tribot.order2_best_recovery_start_amount(
            order1.filled_start_amount, order2.amount, order2.filled)

        order_rec_data = tribot.create_recovery_data(working_triangle["deal-uuid"], working_triangle["cur2"],
                                                     working_triangle["cur1"],
                                                     working_triangle["leg2-recover-amount"],
                                                     working_triangle["leg2-recover-start-curr-best-amount"], 2)

        recovery_data.append(order_rec_data)
        tribot.print_recovery_data(order_rec_data)
        tribot.send_recovery_request(order_rec_data)

        working_triangle["status"] = "Failed 2"
        continue

    tribot.log(tribot.LOG_INFO, "Order2: filled {} with fee {}".format(
        order2.filled_dest_amount, order2.fees[order2.dest_currency]["amount"]))

    # Order 3
    order3_amount = order2.filled_dest_amount - order2.fees[order2.dest_currency]["amount"]

    price3 = tribot.exchange.price_to_precision(working_triangle["symbol3"],
                                                order_books[working_triangle["symbol3"]].get_depth_for_trade_side(
                                                    order3_amount,
                                                    working_triangle["leg3-order"]).total_price)

    tribot.log(tribot.LOG_INFO, "Trade 3/3: from {}-{}->{}".format(working_triangle["cur3"],
                                                                   working_triangle["leg3-order"],
                                                                   working_triangle["cur1"]))

    tribot.log(tribot.LOG_INFO, "Price: {}. Src amount {}".format(price3, order3_amount))

    order3 = tribot.do_trade(working_triangle["symbol3"], working_triangle["cur3"], working_triangle["cur1"],
                             order3_amount, working_triangle["leg3-order"], price3)

    if order3.filled_dest_amount > 0:
        resp_trades = tribot.get_trade_results(order3)
        order3.update_order_from_exchange_resp(resp_trades)
        order3.fees = tribot.exchange.fees_from_order(order3)


        working_triangle["leg3-order-status"] = order3.status

        if order3.filled < order3.amount * 0.9999:
            working_triangle["leg3-order-result"] = "PartFill"

            working_triangle["leg3-recover-amount"] = order3.amount_start - order3.filled_start_amount
            working_triangle["leg3-recover-start-curr-best-amount"] = tribot.order3_best_recovery_start_amount(
                order1.filled_start_amount, order2.amount, order2.filled, order3.amount, order3.filled)

            order_rec_data = tribot.create_recovery_data(working_triangle["deal-uuid"], working_triangle["cur3"],
                                                         working_triangle["cur1"],
                                                         working_triangle["leg3-recover-amount"],
                                                         working_triangle["leg3-recover-start-curr-best-amount"], 3)

            recovery_data.append(order_rec_data)
            tribot.print_recovery_data(order_rec_data)
            tribot.send_recovery_request(order_rec_data)

        else:
            working_triangle["leg3-order-result"] = "Filled"

    else:
        # recover from order3
        working_triangle["leg3-order-result"] = "Failed"
        working_triangle["leg3-order-status"] = order3.status
        working_triangle["leg3-recover-amount"] = order3.amount_start
        working_triangle["leg3-recover-start-curr-best-amount"] = tribot.order3_best_recovery_start_amount(
            order1.filled_start_amount, order2.amount, order2.filled, order3.amount, order3.filled)

        order_rec_data = tribot.create_recovery_data(working_triangle["deal-uuid"], working_triangle["cur3"],
                                                     working_triangle["cur1"],
                                                     working_triangle["leg3-recover-amount"],
                                                     working_triangle["leg3-recover-start-curr-best-amount"], 3)

        recovery_data.append(order_rec_data)
        tribot.print_recovery_data(order_rec_data)
        tribot.send_recovery_request(order_rec_data)
        working_triangle["status"] = "Failed 3"
        continue

    tribot.log(tribot.LOG_INFO, "Order3: filled {} with fee {}".format(
        order3.filled_dest_amount, order3.fees[order3.dest_currency]["amount"]))

    tribot.log(tribot.LOG_INFO, "Result Amount: {}".format(order3.filled_dest_amount))
    tribot.log(tribot.LOG_INFO, "Result Diff: {}".format(order3.filled_dest_amount - order1.filled_start_amount))
    tribot.log(tribot.LOG_INFO, "Result %%: {}".format(order3.filled_dest_amount/order1.filled_start_amount))

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







