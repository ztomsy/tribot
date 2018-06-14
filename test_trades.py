import tkgtri


# eW = tkgtri.ccxtExchangeWrapper.load_from_id("binance",
#                                              "AmEkXUlAh3fW1XkxIOSLovMVia1B55bWI2937Y9ZGRu25uJj2XSCBbOGoI8bb8II",
#                                              "6yy8vrkUR3aOBJyUkzRtEHGYR01gxMmyYJ6jMHyt3HxY7AtXlKr54FmtPOLUsBvh")

eW = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin",
                                             "5b22b10709e5a14f2c125e3d", "11ec0073-8919-4863-a518-7e2468506752")

eW.get_markets()

balance = eW._ccxt.fetch_balance()
# eW.order.place_limit_order_for_start_amount(start_cur, dest_cur, amount_of_start_cur)
# eW.order.time_to_fill = 380 # in seconds
#
# while eW.order.status not in ["filled"]:
#
#     if eW.order.time_from_start > eW.order.time_to_fill:
#
#         eW.order.cancel()
#
#         eW.recover(dest_cur, start_curr, eW.order.filled.dest)
#
#         if eW.status.order == "recovered":
#
#             eW.order_update_status_db()
#
#
#         break
#
#     eW.order.fetch_update()
#
#     eW.order_update_status_db()
#



start_curr= "ETH"
dest_cur = "BTC"
bal_to_bid = 0.1

side = tkgtri.core.get_order_type(start_curr, dest_cur, eW.markets)
symbol = tkgtri.core.get_symbol(start_curr, dest_cur, eW.markets)

ob_array = eW._ccxt.fetch_order_book(symbol)
ob = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array['bids'])

order = tkgtri.TradeOrder(symbol, bal_to_bid, side)
d = order.fake_market_order(ob)

eW.place_limit_order(order.symbol, "limit", side, )


# d = ob.(bal_to_bid, dest_cur)
# price = d.total_price
# amount = d.total_quantity



pass










