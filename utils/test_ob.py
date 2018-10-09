from tkgtri import Deal
from tkgtri import tri_arb as ta
import tkgcore
import ccxt

exchange = ccxt.binance()
exchange.load_markets()

deal = Deal()

deal_id = "e42a895c-4c82-4289-b8bc-7c2e01f03aac"
deal_file = deal_id
ob_file = deal_file


deal.uuid = deal_id
deal.symbols = ["AXPR/ETH", "AXPR/BTC", "ETH/BTC"]

# deal.load_from_csv(deal_file, deal_id)
deal.get_order_books_from_csv(ob_file)

ob = dict()
for i in range(1, 4):
    ob[i] = deal.order_books[deal.symbols[i - 1]]

# within available volumes in order book
max_possible = ta.get_maximum_start_amount(exchange, deal.data_row, ob,1, 10, 0.02)


print("OK")
