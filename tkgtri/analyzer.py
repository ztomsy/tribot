import csv
import collections
import numpy as np
from ztom.orderbook import OrderBook

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





