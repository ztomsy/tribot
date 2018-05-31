import networkx as nx
import numpy as np


#
# todo make ccxt independent - take only active markets and tickers as parameter
#
def get_basic_triangles_from_markets(markets: list):
    graph = nx.Graph()
    for symbol in markets:

        if markets[symbol]["active"]:
            graph.add_edge(markets[symbol]["base"], markets[symbol]["quote"])

    # finding the triangles as the basis cycles in graph
    triangles = list(nx.cycle_basis(graph))




    return triangles

def get_all_triangles(triangles: list, start_currencies: list ):

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
# {"CUR1-CUR2-CUR3": { "triangle": ["CUR1","CUR2","CUR3"],
#                       "symbols": ["CUR2/CUR1","CUR3/CUR2","CUR2/CUR3"],
#                       "orders":["buy","sell", "sell"],
#                       "prices": [price1, price2, price3]
#                       "result": result
#                     }
#
#


def get_triangle_with_tickers(triangle: list, ccxt_tickers: dict):
    # triangle_tickers = dict()
    # s += i: for i in triangle
    #
    # triangle_tickers
    pass


def fill_triangles(triangles: list, start_currencies: list, tickers: dict):
    tri_list = list()

    for t in triangles:
        tri_name = "-".join(t)

        if start_currencies is not None and t[0] in start_currencies:
            tri_dict = dict()

            for i, s_c in enumerate(t):

                source_cur = t[i]
                dest_cur = t[i + 1] if i < len(t) - 1 else t[0]

                if source_cur + "/" + dest_cur in tickers:
                    symbol = source_cur + "/" + dest_cur
                    order_type = "sell"
                    price_type = "bid"

                elif dest_cur + "/" + source_cur in tickers:
                    symbol = dest_cur + "/" + source_cur
                    order_type = "buy"
                    price_type = "ask"

                if symbol in tickers and price_type in tickers[symbol] and tickers[symbol][price_type] > 0:
                    price = tickers[symbol][price_type]

                else:
                    price = None

                leg = i + 1


                tri_dict["triangle"] = tri_name
                tri_dict["cur" + str(leg)] = t[i]
                tri_dict["symbol" + str(leg)] = symbol
                tri_dict["leg{}-order".format(str(leg))] = order_type
                tri_dict["leg{}-price".format(str(leg))] = price

            tri_dict["leg-orders"] = tri_dict["leg1-order"] + "-" + tri_dict["leg2-order"] + "-" + \
                                     tri_dict["leg3-order"]

            tri_list.append(tri_dict)


    return tri_list

