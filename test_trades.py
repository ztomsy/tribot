import tkgtri
import sys

_keys = {"binance":
             {"key": "AmEkXUlAh3fW1XkxIOSLovMVia1B55bWI2937Y9ZGRu25uJj2XSCBbOGoI8bb8II",
              "secret": "6yy8vrkUR3aOBJyUkzRtEHGYR01gxMmyYJ6jMHyt3HxY7AtXlKr54FmtPOLUsBvh"},
         "kucoin":
             {"key": "5b22b10709e5a14f2c125e3d",
              "secret": "11ec0073-8919-4863-a518-7e2468506752"}
         }

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("binance",
#                                              "AmEkXUlAh3fW1XkxIOSLovMVia1B55bWI2937Y9ZGRu25uJj2XSCBbOGoI8bb8II",
#                                              "6yy8vrkUR3aOBJyUkzRtEHGYR01gxMmyYJ6jMHyt3HxY7AtXlKr54FmtPOLUsBvh")

# eW = tkgtri.ccxtExchangeWrapper.load_from_id("kucoin",
#                                              "5b22b10709e5a14f2c125e3d", "11ec0073-8919-4863-a518-7e2468506752")

exchange_id = "kucoin"
start_curr= "ETH"
dest_cur = "BTC"
start_curr_amount = 0.05

eW = tkgtri.ccxtExchangeWrapper.load_from_id(exchange_id, _keys[exchange_id]["key"],
                                             _keys[exchange_id]["secret"])

eW.get_markets()

balance_start_curr = eW._ccxt.fetch_balance()[start_curr]["free"]

symbol = tkgtri.core.get_symbol(start_curr, dest_cur, eW.markets)
side = tkgtri.core.get_order_type(start_curr, dest_cur, symbol)

ob_array = eW._ccxt.fetch_order_book(symbol)
ob = tkgtri.OrderBook(symbol, ob_array["asks"], ob_array['bids'])

d = ob.get_depth_for_destination_currency(start_curr_amount, dest_cur)
price = d.total_price
amount = d.total_quantity / d.total_price if side == "sell" else d.total_quantity

order_resp = eW.place_limit_order(symbol, "limit", side, amount, price )

print(order_resp)
sys.exit(0)
# d = ob.(bal_to_bid, dest_cur)
# price = d.total_price
# amount = d.total_quantity



pass










