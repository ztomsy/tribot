from tkgtri import Deal
from tkgtri import tri_arb as ta
from tkgtri import analyzer
import tkgcore
import ccxt

exchange = ccxt.binance()
exchange.load_markets()

deal = Deal()

deal_id = "c91e6616-dc58-42ff-b06e-f9a47ebb09d3"
deal_file = deal_id + ".csv"
ob_file = deal_id + "_ob.csv"

# analyzer = analyzer.Deal()
deal.load_from_csv(deal_file, deal_id)

#deal.uuid = deal_id
#deal.symbols = ["AXPR/ETH", "AXPR/BTC", "ETH/BTC"]

# deal.load_from_csv(deal_file, deal_id)
deal.get_order_books_from_csv(ob_file)

ob = dict()
for i in range(1, 4):
    ob[i] = deal.order_books[deal.symbols[i - 1]]

# within available volumes in order book
max_possible = ta.get_maximum_start_amount(exchange, deal.data_row, ob, 0.5, 10, 0.002, 1.005)

expected_result = ta.order_book_results(exchange, deal.data_row,
                                        ob, 0.002)

print("OK")
