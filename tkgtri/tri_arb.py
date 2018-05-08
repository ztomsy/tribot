import networkx as nx


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


# output : dict
# {"CUR1-CUR2-CUR3": { "triangle": ["CUR1","CUR2","CUR3"],
#                       "symbols": ["CUR2/CUR1","CUR3/CUR2","CUR2/CUR3"],
#                       "orders":["buy","sell", "sell"],
#                       "prices": [price1, price2, price3]
#                       "result": result
#                     }
#
#
# def fill_triangles(triangles: list, start_currency: list, ccxt_tickers:dict):
#
#     filtered_triangles = list()
#
#     for cur in triangles:
#         if start_currency in cur:
#             p = cur.index(start_currency)
#             if p > 0:
#                 cur = np.roll(cur, 3 - p).tolist()
#
#             filtered_triangles.append(list((start_currency, cur[1], cur[2])))
#             filtered_triangles.append(list((start_currency, cur[2], cur[1])))
#
#     return filtered_triangles
