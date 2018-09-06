import csv
import collections
import numpy as np
from .orderbook import OrderBook


class Analyzer:

    # todo make test
    #
    @staticmethod
    def order_book_results(exchange, deal_row, order_books, start_bid):

        d = dict()

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

        d["result"] = d[3].total_quantity / start_bid

        return d

    # find first occurrence (leg and ticker) of counter oder
    # result - dict r[legX-counter-order-match-ticker] if found
    # False - if not found

    @staticmethod
    def find_counter_order_tickers(past_triangles, max_previous_tickers=5):

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

    @staticmethod
    def get_maximum_start_amount(exchange, data_row, order_books, maximum_bid, intervals=10, start_amount = None):

        if start_amount is None: start_amount = data_row["min-namnt"]

        if maximum_bid > float(start_amount):

            amount_to_check = np.linspace(float(start_amount), maximum_bid, intervals)

            results = list(map(
                lambda x: float(x) * (Analyzer.order_book_results(exchange, data_row, order_books, float(x))["result"] - 1),
                amount_to_check))

            max_result = max(results)
            max_amount = amount_to_check[results.index(max_result)]

        else:
            max_amount = maximum_bid
            max_result = float(max_amount) * (
                    Analyzer.order_book_results(exchange, data_row, order_books, float(max_amount))["result"] - 1)

        return {"amount": max_amount, "result": max_result}


# todo - add tests
class Deal:

    def __init__(self):
        self.data_row = dict()  # as in csv fle
        self.legs = list()
        self.symbols = list() # in order of trades
        self.order_books = collections.defaultdict(dict)  # key is symbol
        self.uuid = None
        self.previous_tickers = list()
        self.all_tickers = list()
        self.real_result = None
        self.start_qty = None

    def parse_from_rows(self):
        self.data_row = self.all_tickers[-1]  # last record is the actual deal record
        self.start_qty = self.data_row["start-qty"]

        for i in range(1, 4):
            self.symbols.append(self.data_row["symbol"+str(i)])

    def load_from_csv(self, file_name, uuid):
        with open(file_name, newline='') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row['deal-uuid'] == uuid:
                    self.all_tickers.append(row)

        self.uuid = uuid
        self.parse_from_rows()

    def get_order_books_from_csv(self, file_name):
        if self.uuid is None:
            return False

        ob_array = collections.defaultdict(dict)

        with open(file_name, newline='') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row['deal-uuid'] == self.uuid:
                    if row["symbol"] not in ob_array:
                        ob_array[row["symbol"]] = collections.defaultdict(dict)
                        ob_array[row["symbol"]]["asks"] = list()
                        ob_array[row["symbol"]]["bids"] = list()

                    ob_array[row["symbol"]]["asks"].append(list([row['ask'], row['ask-qty']]))
                    ob_array[row["symbol"]]["bids"].append(list([row['bid'], row['bid-qty']]))

            for symbol in self.symbols:
                self.order_books[symbol] = OrderBook(symbol, ob_array[symbol]["asks"], ob_array[symbol]["bids"])

            return True





