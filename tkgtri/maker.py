import tkgcore
from tkgcore import core
from tkgcore import ActionOrder, ActionOrderManager
from tkgcore import FokThresholdTakerPriceOrder, FokOrder
import tkgtri
from tkgtri import *
import sys
import time


class SingleTriArbMaker(object):
    """
    class to proceed with orders within the triangular arbitrage
    """

    def __init__(self, currency1: str, currency2: str, currency3: str,
                 price1: float, price2: float, price3: float, start_amount: float, min_amount_currency1: float,
                 symbol1: str, symbol2: str, symbol3: str, commission: float, commission_maker: float,
                 threshold: float,
                 max_order1_updates: int = 2000,
                 max_order2_updates: int = 2000,
                 max_order3_updates: int = 2000,
                 cancel_price_threshold: float = -0.01):

        self.currency1 = currency1
        self.currency2 = currency2
        self.currency3 = currency3

        self.price1 = price1
        self.price2 = price2
        self.price3 = price3

        self.start_amount = start_amount

        self.state = "new"
        """ states: new, order1_create , order1, order2_create, order2, order3_create, order3, finished"""

        self.min_amount_currency1 = min_amount_currency1

        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.symbol3 = symbol3

        self.order1 = None  # type: ActionOrder
        self.order2 = None  # type: FokThresholdTakerPriceOrder
        self.order3 = None  # type: FokThresholdTakerPriceOrder

        self.max_order1_updates = max_order1_updates
        self.max_order2_updates = max_order2_updates
        self.max_order3_updates = max_order3_updates

        self.current_triangle = [[self.currency1, self.currency2, self.currency3]]
        self.commission = commission
        self.commission_maker = commission_maker

        self.threshold = threshold

        self.cancel_taker_price_threshold = cancel_price_threshold

    # @classmethod
    # def create_from_deal_dict(cls, deal_dict:dict):

        self.LOG_DEBUG = "DEBUG"
        self.LOG_INFO = "INFO"
        self.LOG_ERROR = "ERROR"
        self.LOG_CRITICAL = "CRITICAL"

    @staticmethod
    def log(level, msg, msg_list=None):
        if msg_list is None:
            print(level, msg)
        else:
            print(level, msg)
            for line in msg_list:
                print(level, "... " + str(line))

    def use_logger_from(self, src_object):
        self.LOG_DEBUG = src_object.LOG_DEBUG
        self.LOG_INFO = src_object.LOG_INFO
        self.LOG_ERROR = src_object.LOG_ERROR
        self.LOG_CRITICAL = src_object.LOG_CRITICAL

        setattr(self, "log", src_object.log )
        # self.log = src_object.log

    def update_state(self, tickers: dict = None):

        if self.state == "new" and self.order1 is None:

            self.order1 = ActionOrder.create_from_start_amount(symbol=self.symbol1,
                                                               start_currency=self.currency1,
                                                               amount_start=self.start_amount,
                                                               dest_currency=self.currency2,
                                                               price=self.price1,
                                                               max_order_updates=self.max_order1_updates)
            self.state = "order1_create"

            return True

        if self.state == "order1_create" and self.order1.status == "open":
            self.state = "order1"
            # let's proceed directly to the new state

        if self.state == "order1" and self.order1.status == "open":
            tickers_original = tickers
            # substitute ticker prices with order1 price
            tickers[self.order1.symbol]["ask"] = self.order1.get_active_order().price
            tickers[self.order1.symbol]["bid"] = self.order1.get_active_order().price

            current_result = fill_triangles_maker(self.current_triangle, [self.currency1], tickers,
                                                  self.commission,
                                                  self.commission_maker)
            print()
            print("Current result: {result}. Order's price {order_price} Ticker's price {ticker}  ".format(
                result=current_result[0]["result"], order_price=self.order1.price,
                ticker=tickers_original[self.order1.symbol][
                    current_result[0]["leg1-price-type"]
                ]))
            print()

            if current_result[0]["result"] < self.threshold:
                self.log(self.LOG_INFO,
                         "Result is below threshold {}. Forcing cancellation of the order.".format(
                               current_result[0]["result"]))

                self.order1.force_close()

            return True

        if self.state == "order1" and self.order1.status == "closed" and self.order1.filled == 0:
            self.state = "finished"
            return True

        if self.state == "order1" and self.order1.status == "closed" and self.order2 is None:

            self.order2 = FokThresholdTakerPriceOrder.create_from_start_amount(
                symbol=self.symbol2,
                start_currency=self.currency2,
                amount_start=self.order1.filled_dest_amount,
                dest_currency=self.currency3,
                price=self.price2,
                max_order_updates=self.max_order2_updates,
                taker_price_threshold=self.cancel_taker_price_threshold,
                threshold_check_after_updates=self.max_order2_updates)

            self.state = "order2_create"
            return True

        if self.state == "order2_create" and self.order2.status == "open":
            self.state = "order2"
            # let's proceed directly to the new state

        if self.state == "order2" and self.order2.status == "closed" and self.order2.filled == 0:
            self.state = "finished"
            return True

        if self.state == "order2" and self.order2.status == "closed" and self.order3 is None:
            self.state = "order3_create"

            self.order3 = FokThresholdTakerPriceOrder.create_from_start_amount(
                symbol=self.symbol3,
                start_currency=self.currency3,
                amount_start=self.order2.filled_dest_amount,
                dest_currency=self.currency1,
                price=self.price3,
                max_order_updates=self.max_order3_updates,
                taker_price_threshold=self.cancel_taker_price_threshold,
                threshold_check_after_updates=self.max_order3_updates)

            return True

        if self.state == "order3_create" and self.order3.status == "open":
            self.state = "order3"
            # let's proceed directly to the new state

        if self.state == "order3" and self.order3.status == "closed":
            self.state = "finished"
            return True
