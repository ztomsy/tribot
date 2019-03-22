import tkgcore
from tkgcore import core
import tkgtri
import sys
import time


def fill_triangles_maker(triangles: list, start_currencies: list, tickers: dict, commission=0, commission_maker = 0):
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
                        result = result * (1-commission) if leg != 1 else result * (1-commission_maker)

                    ticker_qty = tickers[symbol][price_type+'Volume']

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
                                                  tickers[symbol][price_type+'Volume'],
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
tribot.commission_maker = None

tribot.set_from_cli(sys.argv[1:])  # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename)  # config taken from cli or default

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

start_index = 0
start_amount = 0.01
om = tkgcore.ActionOrderManager(tribot.exchange)
om.request_trades = False

while True:
    if om.pending_actions_number() == 0:
        sleep_time = tribot.exchange.requests_throttle.sleep_time()
        print("Sleeping for {}s".format(sleep_time))
        time.sleep(sleep_time)

    tickers = tribot.fetch_tickers()
    tribot.set_triangles()

    tribot.proceed_triangles()
    good_taker_triangles = tribot.get_good_triangles()
    results_taker = sorted(tribot.tri_list, key=lambda k: k['result'], reverse=True)

    results_maker = fill_triangles_maker(tribot.all_triangles, tribot.start_currency, tickers, tribot.commission,
                                         tribot.commission_maker)
    # results_maker = sorted(results_maker, key=lambda k: k['result'], reverse=True)
    good_maker_triangles = tribot.get_good_triangles(results_maker)
    good_maker_triangles = sorted(good_maker_triangles, key=lambda k: k['leg1-cur1-qty'], reverse=False)

    print("Good TAKER triangles: {}. Best TAKER triangle {}".format(len(good_taker_triangles), results_taker[0]["result"]))

    print("Good MAKER triangles: {}. Best MAKER triangle {} result {}" .format(len(good_maker_triangles),
                                                                               results_maker[0]["symbol1"],
                                                                               results_maker[0]["result"]))

    print("TOP 5 MAKER triangles: ")
    if len(good_maker_triangles) > 0:
        top_to_display = 100 if len(good_maker_triangles) > 100 else len(good_maker_triangles)

        print("TOP {} MAKER triangles: ".format(top_to_display))

        for i in range(0, top_to_display):
            print(good_maker_triangles[i]["triangle"], " ", good_maker_triangles[i]["result"], " ", good_maker_triangles[i]["leg1-cur1-qty"])

    if len(good_maker_triangles) < start_index + 1:
        continue

    if good_maker_triangles[start_index]["leg1-cur1-qty"] / start_amount > 70:
        print("Leg1 qty / start_amount is too much {}".format(good_maker_triangles[start_index]["leg1-cur1-qty"] / start_amount))
        continue

    current_triangle = [[good_maker_triangles[start_index]["cur1"], good_maker_triangles[start_index]["cur2"],
                        good_maker_triangles[start_index]["cur3"]]]


    if tribot.debug:
        continue

    order1 = tkgcore.ActionOrder\
        .create_from_start_amount(symbol=good_maker_triangles[start_index]["symbol1"],
                                  start_currency=good_maker_triangles[start_index]["cur1"],
                                  amount_start=start_amount,
                                  dest_currency=good_maker_triangles[start_index]["cur2"],
                                  price=good_maker_triangles[start_index]["leg1-price"],
                                  max_order_updates=2000)

    om.add_order(order1)

    while len(om.get_open_orders()) > 0:

        tickers = tribot.fetch_tickers()
        tickers_original = tickers
        # substitute ticker prices with order1 price
        tickers[order1.symbol]["ask"] = order1.get_active_order().price
        tickers[order1.symbol]["bid"] = order1.get_active_order().price

        current_result = fill_triangles_maker(current_triangle, [current_triangle[0][0]], tickers, tribot.commission,

                                              tribot.commission_maker)
        print()
        print("Current result: {result}. Order's price {order_price} Ticker's price {ticker}  ".format(
            result=current_result[0]["result"], order_price = order1.price, ticker = tickers_original[order1.symbol][
                current_result[0]["leg1-price-type"]
            ]))
        print()

        if current_result[0]["result"] < tribot.threshold:
            tribot.log(tribot.LOG_INFO,
                       "Result is below threshold {}. Forcing cancellation of the order.".format(current_result[0]["result"]))

            order1.force_close()

        om.proceed_orders()

        if om.pending_actions_number() == 0 and om.get_closed_orders() is None:
            sleep_time = tribot.exchange.requests_throttle.sleep_time()
            print("Sleeping for {}s".format(sleep_time))
            time.sleep(sleep_time)

    if order1.filled_start_amount <= 0.003:
        continue

    order2 = tkgcore.FokThresholdTakerPriceOrder.\
        create_from_start_amount(symbol=good_maker_triangles[start_index]["symbol2"],
                                 start_currency=good_maker_triangles[start_index]["cur2"],
                                 amount_start=order1.filled_dest_amount,
                                 dest_currency=good_maker_triangles[start_index]["cur3"],
                                 price=good_maker_triangles[start_index]["leg2-price"],
                                 max_order_updates=10000000000,
                                 taker_price_threshold=-0.01,
                                 threshold_check_after_updates=1000)

    om.add_order(order2)

    while len(om.get_open_orders()) > 0:

        om.proceed_orders()

        if om.pending_actions_number() == 0 and om.get_closed_orders() is None:

            sleep_time = tribot.exchange.requests_throttle.sleep_time()
            print("Sleeping for {}s".format(sleep_time))
            time.sleep(sleep_time)

    if core.convert_currency(order2.dest_currency, order2.filled_dest_amount,
                             "BTC", core.get_symbol("BTC", order2.dest_currency, tickers),
                             ticker=tickers[core.get_symbol("BTC", order2.dest_currency, tickers)]) < 0.003:

        sys.exit()

    order3 = tkgcore.FokThresholdTakerPriceOrder. \
        create_from_start_amount(symbol=good_maker_triangles[start_index]["symbol3"],
                                 start_currency=good_maker_triangles[start_index]["cur3"],
                                 amount_start=order2.filled_dest_amount,
                                 dest_currency=good_maker_triangles[start_index]["cur1"],
                                 price=good_maker_triangles[start_index]["leg3-price"],
                                 max_order_updates=100000,
                                 taker_price_threshold=-0.01,
                                 threshold_check_after_updates=5000)

    om.add_order(order3)

    while len(om.get_open_orders()) > 0:
        om.proceed_orders()

        if om.pending_actions_number() == 0:
            sleep_time = tribot.exchange.requests_throttle.sleep_time()
            print("Sleeping for {}s".format(sleep_time))
            time.sleep(sleep_time)


    print("Result: {}".format(order3.filled_dest_amount - order1.filled_start_amount))
    sys.exit()

sys.exit()

