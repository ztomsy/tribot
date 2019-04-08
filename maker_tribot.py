import tkgcore
from tkgcore import ActionOrder, FokOrder, FokThresholdTakerPriceOrder
from tkgcore import core
import tkgtri
from tkgtri import SingleTriArbMakerDeal, TriArbMakerCollection
import sys
import time
from tkgcore import DealReport
import datetime
import pytz


def fill_triangles_maker(triangles: list, start_currencies: list, tickers: dict, commission=0, commission_maker=0):
    tri_list = list()

    for t in triangles:
        tri_name = "-".join(t)

        if start_currencies is not None and t[0] in start_currencies:
            tri_dict = dict()
            result = 1.0

            for i, s_c in enumerate(t):

                leg = i + 1

                source_cur = t[i]
                dest_cur = t[i + 1] if i < len(t) - 1 else t[0]

                symbol = ""
                order_type = ""
                price_type = ""

                if source_cur + "/" + dest_cur in tickers:
                    symbol = source_cur + "/" + dest_cur
                    order_type = "sell"
                    price_type = "bid" if leg != 1 else "ask"

                elif dest_cur + "/" + source_cur in tickers:
                    symbol = dest_cur + "/" + source_cur
                    order_type = "buy"
                    price_type = "ask" if leg != 1 else "bid"

                if symbol in tickers and price_type in tickers[symbol] and tickers[symbol][price_type] is not None \
                        and tickers[symbol][price_type] > 0:

                    price = tickers[symbol][price_type]

                    if result != 0:
                        result = result / price if order_type == "buy" else result * price
                        result = result * (1 - commission) if leg != 1 else result * (1 - commission_maker)

                    ticker_qty = tickers[symbol][price_type + 'Volume']

                else:
                    price = 0
                    result = 0
                    ticker_qty = 0

                tri_dict["triangle"] = tri_name
                tri_dict["cur" + str(leg)] = t[i]
                tri_dict["symbol" + str(leg)] = symbol
                tri_dict["leg{}-order".format(str(leg))] = order_type
                tri_dict["leg{}-price".format(str(leg))] = price
                tri_dict["leg{}-price-type".format(str(leg))] = price_type

                tri_dict["leg{}-ticker-qty".format(str(leg))] = ticker_qty

                # getting amount of ticker qty in start cur
                currency_of_amount_in_ticker = symbol.split("/")[0]

                if currency_of_amount_in_ticker and currency_of_amount_in_ticker != t[0]:

                    if leg == 2:
                        symbol_to_convert = core.get_symbol(currency_of_amount_in_ticker, t[0], tickers)
                    else:
                        symbol_to_convert = symbol
                    try:
                        tri_dict["leg{}-cur1-qty".format(str(leg))] = \
                            core.convert_currency(currency_of_amount_in_ticker,
                                                  tickers[symbol][price_type + 'Volume'],
                                                  t[0],
                                                  symbol=symbol_to_convert,
                                                  price=price)
                    except:
                        tri_dict["leg{}-cur1-qty".format(str(leg))] = 999999999

                else:
                    tri_dict["leg{}-cur1-qty".format(str(leg))] = ticker_qty

            if result != 0:
                tri_dict["leg-orders"] = tri_dict["leg1-order"] + "-" + tri_dict["leg2-order"] + "-" + \
                                         tri_dict["leg3-order"]

            tri_dict["result"] = result

            tri_list.append(tri_dict)

    return tri_list


tribot = tkgtri.tribot.TriBot("_config_def_maker.json")

# adding these fields in order to get them from config
tribot.commission_maker = 0.0
tribot.start_amount = 0
tribot.max_deals = 0

tribot.set_from_cli(sys.argv[1:])  # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename)  # config taken from cli or default

tribot.init_remote_reports()

try:
    tribot.init_exchange()
    # init offline mode
    if tribot.offline:
        tribot.offline_tickers_file = "test_data/tickers_maker.csv"

        tribot.init_offline_mode()  # set offline files from the cli or config
        tribot.exchange.offline_use_last_tickers = True

        tribot.log(tribot.LOG_INFO, "Offline Mode")
        tribot.log(tribot.LOG_INFO, "..markets file: {}".format(tribot.offline_markets_file))
        tribot.log(tribot.LOG_INFO, "..tickers file: {}".format(tribot.offline_tickers_file))
        if tribot.offline_order_books_file:
            tribot.log(tribot.LOG_INFO, "..order books file: {}".format(tribot.offline_order_books_file))
        else:
            tribot.log(tribot.LOG_INFO, "..order books will be created from tickers")

        if tribot.offline_run_test:
            tribot.init_test_run()

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

# fetching the balance for first start currency or taking test balance from the cli/config
try:
    tribot.log(tribot.LOG_INFO, "Fetching balance...")
    tribot.load_balance()
    tribot.log(tribot.LOG_INFO, "Init Balance: {}".format(tribot.balance))

except Exception as e:
    tribot.log(tribot.LOG_ERROR, "Error while fetching balance {}".format(tribot.exchange_id))
    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)
    tribot.log(tribot.LOG_ERROR, "Exiting")
    sys.exit("666")

# start_index = tribot.start_amount
start_amount = tribot.start_amount

om = tkgcore.ActionOrderManager(tribot.exchange)
om.request_trades = False

tribot.set_triangles()

triarb_collection = TriArbMakerCollection(max_deals=tribot.max_deals)

while True:

    if om.pending_actions_number() == 0:
        sleep_time = tribot.exchange.requests_throttle.sleep_time()
        print("Sleeping for {}s".format(sleep_time))
        time.sleep(sleep_time)
    else:
        print("!!! NO SLEEP. ACTIONS ARE PENDING !!!")

    try:
        tickers = tribot.fetch_tickers()
    except Exception  as e:
        tribot.log(tribot.LOG_ERROR, "Could not get tickers...")
        tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
        tribot.log(tribot.LOG_ERROR, e.args)

        continue

    # remove finished deals
    # for deal in triarb_collection.deals:
    #     if deal.state == "finished":
    #         triarb_collection.remove_deal(deal.uuid)

    # process orders via order manager
    om.data_for_orders["tickers"] = tickers
    om.proceed_orders()

    # remove finished deals
    deals_removed = triarb_collection.bulk_remove()
    tribot.log(tribot.LOG_INFO, "Deals removed: {}".format(deals_removed))

    # proceed with the current deals
    for single_trimaker_deal in triarb_collection.deals:
        single_trimaker_deal.update_state(tickers)

        # order1 has been created when the deal was created (see below)

        # creating order2
        if single_trimaker_deal.state == "order2_create":
            order2 = single_trimaker_deal.order2
            om.add_order(order2)

        # finished after order 2 which was not filled at all, so we will recover
        if single_trimaker_deal.state == "finished" and single_trimaker_deal.order2 is not None and \
                single_trimaker_deal.order2.filled == 0 and single_trimaker_deal.leg2_recovery_amount > 0 and \
                single_trimaker_deal.order3 is None:
            order_rec_data = tribot.create_recovery_data(single_trimaker_deal.uuid,
                                                         single_trimaker_deal.currency2,
                                                         single_trimaker_deal.currency1,
                                                         single_trimaker_deal.leg2_recovery_amount,
                                                         single_trimaker_deal.leg2_recovery_target, 2)

            tribot.print_recovery_data(order_rec_data)
            tribot.send_recovery_request(order_rec_data)

        # adding order3 and check if we need to recovery from 2nd order
        if single_trimaker_deal.state == "order3_create":
            order3 = single_trimaker_deal.order3
            om.add_order(order3)

            # check if we need to recover from order 2
            if single_trimaker_deal.order2.filled < single_trimaker_deal.order2.amount * 0.9999:
                order_rec_data = tribot.create_recovery_data(single_trimaker_deal.uuid,
                                                             single_trimaker_deal.currency2,
                                                             single_trimaker_deal.currency1,
                                                             single_trimaker_deal.leg2_recovery_amount,
                                                             single_trimaker_deal.leg2_recovery_target, 2)

                tribot.print_recovery_data(order_rec_data)
                tribot.send_recovery_request(order_rec_data)

        # finish after order 3
        if single_trimaker_deal.state == "finished" and single_trimaker_deal.order3 is not None \
                and single_trimaker_deal.order3.status == "closed":

            if single_trimaker_deal.order3.filled < single_trimaker_deal.order3.amount * 0.9999:
                order_rec_data = tribot.create_recovery_data(single_trimaker_deal.uuid,
                                                             single_trimaker_deal.currency3,
                                                             single_trimaker_deal.currency1,
                                                             single_trimaker_deal.leg3_recovery_amount,
                                                             single_trimaker_deal.leg3_recovery_target, 3)

                tribot.print_recovery_data(order_rec_data)
                tribot.send_recovery_request(order_rec_data)

        if single_trimaker_deal.state == "finished":
            if single_trimaker_deal.order3 is not None:
                print("Result: {}".format(single_trimaker_deal.order3.filled_dest_amount -
                                          single_trimaker_deal.order1.filled_start_amount))
                print()

            if single_trimaker_deal.order1 is not None:
                print("Order1. Filled {}. Report: {}".format(single_trimaker_deal.order1.filled,
                                                             single_trimaker_deal.order1.report()))
                print()

            if single_trimaker_deal.order2 is not None:
                print("Order2. Filled {}. Report: {}".format(single_trimaker_deal.order2.filled,
                                                             single_trimaker_deal.order2.report()))
                print()

            if single_trimaker_deal.order3 is not None:
                print("Order3. Filled {}. Report: {}".format(single_trimaker_deal.order3.filled,
                                                             single_trimaker_deal.order3.report()))
                print()

            if not tribot.sqla["enabled"]:
                triarb_collection.add_bulk_remove(single_trimaker_deal.uuid)
                tribot.log(tribot.LOG_INFO, "Removed deal {} from deals collection".format(single_trimaker_deal.uuid))

            else:
                try:

                    report_sqla = DealReport(
                        timestamp=datetime.datetime.now(tz=pytz.timezone('UTC')),
                        timestamp_start=datetime.datetime.now(tz=pytz.timezone('UTC')),
                        exchange=tribot.exchange_id,
                        instance=tribot.server_id,
                        server=tribot.server_id,
                        deal_type="triarb_maker",
                        deal_uuid=single_trimaker_deal.uuid,
                        status=single_trimaker_deal.status,
                        currency=single_trimaker_deal.currency1,
                        start_amount=single_trimaker_deal.filled_start_amount,
                        result_amount=single_trimaker_deal.result_amount,
                        gross_profit=single_trimaker_deal.gross_profit,
                        net_profit=0.0,
                        config=tribot.get_config_report(),
                        deal_data={}
                    )

                    tribot.sqla_reporter.session.add(report_sqla)
                    tribot.sqla_reporter.session.commit()

                    triarb_collection.add_bulk_remove(single_trimaker_deal.uuid)
                    tribot.log(tribot.LOG_INFO,
                               "Removed deal {} from deals collection".format(single_trimaker_deal.uuid))

                except Exception as e:
                    tribot.log(tribot.LOG_ERROR, "Could not send SQLa report")
                    tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
                    tribot.log(tribot.LOG_ERROR, "Exception body:", e.args)

    # check if we going to exit
    if tribot.run_once and len(triarb_collection.deals) == 0 and len(om.get_open_orders()) == 0 \
            and triarb_collection.total_deals_added >= triarb_collection.max_deals:
        tribot.log(tribot.LOG_INFO, "Exiting because of runonce")
        sys.exit()

    if tribot.run_once and triarb_collection.total_deals_added >= triarb_collection.max_deals:
        continue

    # process new triangles if there is no pending actions
    if om.pending_actions_number() == 0:
        # sleep_time = tribot.exchange.requests_throttle.sleep_time()
        print("Procceeding to triangles...")
        # time.sleep(sleep_time)
    else:
        print("!!! NO Triangles. ACTIONS ARE PENDING !!!")
        continue

    tribot.proceed_triangles()
    good_taker_triangles = tribot.get_good_triangles()
    results_taker = sorted(tribot.tri_list, key=lambda k: k['result'], reverse=True)

    results_maker = fill_triangles_maker(tribot.all_triangles, tribot.start_currency, tickers, tribot.commission,
                                         tribot.commission_maker)
    # results_maker = sorted(results_maker, key=lambda k: k['result'], reverse=True)
    good_maker_triangles = tribot.get_good_triangles(results_maker)
    good_maker_triangles = sorted(good_maker_triangles, key=lambda k: k['leg1-cur1-qty'], reverse=False)

    print("Good TAKER triangles: {}. Best TAKER triangle {}".format(len(good_taker_triangles),
                                                                    results_taker[0]["result"]))

    print("Good MAKER triangles: {}. Best MAKER triangle {} result {}".format(len(good_maker_triangles),
                                                                              results_maker[0]["symbol1"],
                                                                              results_maker[0]["result"]))

    print("TOP 5 MAKER triangles: ")
    if len(good_maker_triangles) > 0:
        top_to_display = 100 if len(good_maker_triangles) > 100 else len(good_maker_triangles)

        print("TOP {} MAKER triangles: ".format(top_to_display))

        for i in range(0, top_to_display):
            print(good_maker_triangles[i]["triangle"], " ", good_maker_triangles[i]["result"], " ",
                  good_maker_triangles[i]["leg1-cur1-qty"])

    # if len(good_maker_triangles) < start_index + 1:
    #     continue

    if len(triarb_collection.deals) >= triarb_collection.max_deals:
        continue

    for good_triangle in good_maker_triangles:

        if good_triangle["leg1-cur1-qty"] > 2:
            print("Leg1 qty / start_amount is too much {}".format(
                good_triangle["leg1-cur1-qty"]))
            continue

        current_triangle = [[good_triangle["cur1"], good_triangle["cur2"],
                             good_triangle["cur3"]]]

        if tribot.debug:
            continue

        # good_triangle = good_maker_triangles[start_index]

        if len(triarb_collection.deals) >= triarb_collection.max_deals:
            tribot.log(tribot.LOG_INFO, "Will not add deal: too many active  {}".format(len(triarb_collection.deals)))
            continue

        new_single_trimaker_deal = SingleTriArbMakerDeal(currency1=good_triangle["cur1"],
                                                         currency2=good_triangle["cur2"],
                                                         currency3=good_triangle["cur3"],
                                                         price1=good_triangle["leg1-price"],
                                                         price2=good_triangle["leg2-price"],
                                                         price3=good_triangle["leg3-price"],
                                                         start_amount=start_amount,
                                                         min_amount_currency1=0.003,
                                                         symbol1=good_triangle["symbol1"],
                                                         symbol2=good_triangle["symbol2"],
                                                         symbol3=good_triangle["symbol3"],
                                                         commission=tribot.commission,
                                                         commission_maker=tribot.commission_maker,
                                                         threshold=tribot.threshold,
                                                         max_order1_updates=1000,
                                                         max_order2_updates=30,
                                                         max_order3_updates=30,
                                                         recover_factor_order2=tribot.recover_factor,
                                                         recover_factor_order3=tribot.recover_factor,
                                                         cancel_price_threshold=tribot.cancel_price_threshold)

        ok_to_add = triarb_collection.ok_to_add(new_single_trimaker_deal)
        if ok_to_add != "OK":
            tribot.log(tribot.LOG_INFO, "Deal could not be added: {}".format(ok_to_add))
            continue

        try:
            triarb_collection.add_deal(new_single_trimaker_deal)
            tribot.log(tribot.LOG_INFO, "Triangle added: {} with uuid {}".format(new_single_trimaker_deal.current_triangle,
                                                                              new_single_trimaker_deal.uuid))

            # update state of created deal
            new_single_trimaker_deal.update_state(tickers)

            # now we have order1 created
            om.add_order(new_single_trimaker_deal.order1)

        except Exception as e:
            tribot.log(tribot.LOG_ERROR, "Could not add deal to collection...")
            tribot.log(tribot.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            tribot.log(tribot.LOG_ERROR, e.args)

sys.exit()
