import networkx as nx
import numpy as np


#
# todo make ccxt independent - take only active markets and tickers as parameter
#
def get_basic_triangles_from_markets(markets):
    graph = nx.Graph()
    for symbol in markets:

        if markets[symbol]["active"]:
            graph.add_edge(markets[symbol]['base'], markets[symbol]['quote'])

    # finding the triangles as the basis cycles in graph
    triangles = list(nx.cycle_basis(graph))

    return triangles


def get_all_triangles(triangles: list, start_currencies: list):

    filtered_triangles = list()

    for start_currency in start_currencies:
        for cur in triangles:
            if start_currency in cur:
                p = cur.index(start_currency)
                if p > 0:
                    cur = np.roll(cur, 3 - p).tolist()

                filtered_triangles.append(list((start_currency, cur[1], cur[2])))
                filtered_triangles.append(list((start_currency, cur[2], cur[1])))

    return filtered_triangles


# output : dict
# {"CUR1-CUR2-CUR3": { "triangle": "CUR1","CUR2","CUR3",
#                       "symbol1": "CUR1/CUR2",
#                       "orders":["buy","sell", "sell"],
#                       "prices": [price1, price2, price3]
#                       "result": result
#                     }

def fill_triangles(triangles: list, start_currencies: list, tickers: dict, commission=0):
    tri_list = list()

    for t in triangles:
        tri_name = "-".join(t)

        if start_currencies is not None and t[0] in start_currencies:
            tri_dict = dict()
            result = 1.0

            for i, s_c in enumerate(t):

                source_cur = t[i]
                dest_cur = t[i + 1] if i < len(t) - 1 else t[0]

                symbol = ""
                order_type = ""
                price_type = ""

                if source_cur + "/" + dest_cur in tickers:
                    symbol = source_cur + "/" + dest_cur
                    order_type = "sell"
                    price_type = "bid"

                elif dest_cur + "/" + source_cur in tickers:
                    symbol = dest_cur + "/" + source_cur
                    order_type = "buy"
                    price_type = "ask"

                if symbol in tickers and price_type in tickers[symbol] and tickers[symbol][price_type] is not None \
                        and tickers[symbol][price_type] > 0:

                    price = tickers[symbol][price_type]

                    if result != 0:
                        result = result / price if order_type == "buy" else result * price
                        result = result * (1-commission)

                else:
                    price = 0
                    result = 0

                leg = i + 1

                tri_dict["triangle"] = tri_name
                tri_dict["cur" + str(leg)] = t[i]
                tri_dict["symbol" + str(leg)] = symbol
                tri_dict["leg{}-order".format(str(leg))] = order_type
                tri_dict["leg{}-price".format(str(leg))] = price

            if result != 0:
                tri_dict["leg-orders"] = tri_dict["leg1-order"] + "-" + tri_dict["leg2-order"] + "-" + \
                                         tri_dict["leg3-order"]

            tri_dict["result"] = result

            tri_list.append(tri_dict)

    return tri_list


def order_book_results(exchange, deal_row, order_books, start_bid):
    """
    get result of tri_arb from 3 order books. In case that some of Order Book will not have enought depth for
    filling - it could take maximum amount of provided order book

    :param exchange: ccxtExcangeWrapper
    :param deal_row: working triangle
    :param order_books: dict of order books (starting from index 1  {1: OrderBook, 2: OrderBook , 3: OrderBook}
    :param start_bid: starging bid of trianlge
    :return d:  dict of results of tri arb calculation
        d["result"] = d[3].total_quantity / (start_bid * total_filled_share)
        d["total_filled_share"] = total_filled_share
        d["result_amount"] = d[3].total_quantity
        d["result_diff"] = d[3].total_quantity - (start_bid * total_filled_share)
        d["filled_start_amount"] = start_bid * total_filled_share

    :return result:
    """

    d = dict()
    total_filled_share = 1.0

    for i in range(1, 4):
        # ob[i] = get_order_book(deal["symbol"+str(i)], bid1_lots, deal["leg"+str(i)+"-order"])

        if i == 1:
            bid_qty = start_bid

        else:
            bid_qty = d[i - 1].total_quantity

        if deal_row["leg" + str(i) + "-order"] == "buy":
            d[i] = order_books[i].get_depth(bid_qty, "buy", "quote")
            d[i].total_quantity = float(exchange.amount_to_precision(deal_row["symbol" + str(i)], d[i].total_quantity))

        if deal_row["leg" + str(i) + "-order"] == "sell":
            d[i] = order_books[i].get_depth(bid_qty, "sell", "base")
            d[i].total_quantity = float(
                exchange.price_to_precision(deal_row["symbol" + str(i)], d[i].total_quantity))

        d[i].total_price = float(exchange.price_to_precision(deal_row["symbol" + str(i)], d[i].total_price))
        total_filled_share = total_filled_share * d[i].filled_share

    d["result"] = d[3].total_quantity / (start_bid * total_filled_share)
    d["total_filled_share"] = total_filled_share
    d["result_amount"] = d[3].total_quantity
    d["result_diff"] = d[3].total_quantity - (start_bid * total_filled_share)
    d["filled_start_amount"] = start_bid * total_filled_share
    return d


def find_counter_order_tickers(past_triangles, max_previous_tickers=5):
    """
    find first occurrence (leg and ticker) of counter oder
    result - dict r[legX-counter-order-match-ticker] if found
    False - if not found

    :param past_triangles:
    :param max_previous_tickers:
    :return:
    """

    r = dict()

    for i in range(len(past_triangles)-1, len(past_triangles)-1-max_previous_tickers, -1):

        ticker = past_triangles[i]["ticker"]

        for j in range(1, 4):

            leg = "leg"+str(j)

            #
            # if we're going to buy (sell) , so we are looking for prices from who are selling [asl] (sell/bid)
            # if bid (ask) price is greater that ask (bid)  price - means that counter order in place
            # https://tkg-base.atlassian.net/wiki/spaces/WORK/pages/65503234/2018-02-07
            #

            if past_triangles[i][leg+"-order"] == "buy":
                if past_triangles[i][leg+"-counter-price"] >= past_triangles[len(past_triangles)-1][leg+"-price"]:
                    if leg+"-counter-order-match-ticker" not in r :
                        r[leg+"-counter-order-match-ticker"] = ticker
                        return r

            if past_triangles[i][leg+"-order"] == "sell":
                if past_triangles[i][leg+"-counter-price"] <= past_triangles[len(past_triangles)-1][leg+"-price"]:
                    if leg + "-counter-order-match-ticker" not in r:
                        r[leg+"-counter-order-match-ticker"] = ticker
                        return r

    return False


def get_maximum_start_amount(exchange, data_row, order_books, maximum_bid, intervals=10, start_amount=None,
                             results_filter=0.0):

    if start_amount is None:
        start_amount = data_row["min-namnt"]  # legacy code for binance market orders

    if maximum_bid > float(start_amount):

        amount_to_check = np.linspace(float(start_amount), maximum_bid, intervals)

        results = map(
            lambda x: (order_book_results(exchange, data_row, order_books, float(x))),
            amount_to_check)

        results = list(filter(lambda x:  x["result"] >= results_filter, results))

        if len(results) > 0:
            max_result_dict = max(results, key=lambda x: x["result_diff"])  # max results dict from order books
        else:
            return None

    else:
        max_result_dict = order_book_results(exchange, data_row, order_books, float(maximum_bid))

    max_result = max_result_dict["result"]
    max_start_amount = max_result_dict["filled_start_amount"]

    return {"amount": max_start_amount, "result": max_result}


