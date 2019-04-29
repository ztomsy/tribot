import ztom
from ztom import ActionOrder, ActionOrderManager
from ztom import FokThresholdTakerPriceOrder, FokOrder
from tkgtri import *
import copy
import uuid as uuid_lib
from typing import List


class SingleTriArbMakerDeal(object):
    """
    class to proceed with orders within the triangular arbitrage with maker first order
    """

    def __init__(self, currency1: str, currency2: str, currency3: str,
                 price1: float, price2: float, price3: float, start_amount: float, min_amount_currency1: float,
                 symbol1: str, symbol2: str, symbol3: str, commission: float, commission_maker: float,
                 threshold: float,
                 max_order1_updates: int = 2000,
                 max_order2_updates: int = 2000,
                 max_order3_updates: int = 2000,
                 recover_factor_order2: float = 1.0,
                 recover_factor_order3: float = 1.0,
                 cancel_price_threshold: float = -0.01,
                 uuid: str = None):

        self.uuid = str(uuid_lib.uuid4()) if uuid is None else uuid

        self.currency1 = currency1
        self.currency2 = currency2
        self.currency3 = currency3

        self.price1 = price1
        self.price2 = price2
        self.price3 = price3

        self.start_amount = start_amount
        self.status = ""
        """
        final status of deal:
        OK, InRecovery, Failed   
        """

        self.state = "new"
        """ current state of deal: 
            new, order1_create , order1, order2_create, order2, order3_create, order3, finished"""

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

        self.recover_factor_order2 = recover_factor_order2
        self.recover_factor_order3 = recover_factor_order3

        self.leg2_recovery_amount = 0.0
        self.leg2_recovery_target = 0.0

        self.leg3_recovery_amount = 0.0
        self.leg3_recovery_target = 0.0

        self.filled_start_amount = 0.0
        """
        filled amount of first maker leg
        """

        self.result_amount = 0.0
        """
        amount of filled currency1 after 3rd leg
        """

        self.gross_profit = 0.0
        """
        gross profit
        """



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

    def update_state(self, tickers_from_exchange: dict = None):
        tickers = copy.deepcopy(tickers_from_exchange)

        #order1_create
        if self.state == "new" and self.order1 is None:

            self.order1 = FokOrder.create_from_start_amount(symbol=self.symbol1,
                                                               start_currency=self.currency1,
                                                               amount_start=self.start_amount,
                                                               dest_currency=self.currency2,
                                                               price=self.price1,
                                                               max_order_updates=self.max_order1_updates,
                                                               )
            self.state = "order1_create"

            return True
        # order1 open
        if self.state == "order1_create" and (self.order1.status == "open" or self.order1.status == "closed"):
            self.state = "order1"
            # let's proceed directly to the new state

        # order1 open
        if self.state == "order1" and self.order1.status == "open":
            # tickers_original = copy.deepcopy(tickers)
            # substitute ticker prices with order1 price
            self.state = "order1"

            tickers[self.order1.symbol]["ask"] = self.order1.get_active_order().price
            tickers[self.order1.symbol]["bid"] = self.order1.get_active_order().price

            current_result = fill_triangles_maker(self.current_triangle, [self.currency1], tickers,
                                                  self.commission,
                                                  self.commission_maker)
            print()
            print("Current result: {result}. Order's price {order_price} Ticker's price {ticker}  ".format(
                result=current_result[0]["result"], order_price=self.order1.price,
                ticker=tickers_from_exchange[self.order1.symbol][
                    current_result[0]["leg1-price-type"]
                ]))
            print()

            if current_result[0]["result"] < self.threshold:
                self.log(self.LOG_INFO,
                         "Result is below threshold {}. Forcing cancellation of the order.".format(
                               current_result[0]["result"]))

                self.order1.force_close()

            return True

        # order1 not filled at all
        if self.state == "order1" and self.order1.status == "closed" and self.order1.filled == 0:
            self.state = "finished"

            self.finish_deal()

            return True

        # order2_create
        if self.state == "order1" and self.order1.status == "closed" and self.order2 is None:

            self.order2 = FokThresholdTakerPriceOrder.create_from_start_amount(
                symbol=self.symbol2,
                start_currency=self.currency2,
                amount_start=self.order1.filled_dest_amount,
                dest_currency=self.currency3,
                price=self.price2,
                max_order_updates=self.max_order2_updates,
                taker_price_threshold=self.cancel_taker_price_threshold,
                threshold_check_after_updates=50)

            self.state = "order2_create"
            return True

        # order2 open
        if self.state == "order2_create" and (self.order2.status == "open" or self.order2.status == "closed"):
            self.state = "order2"
            # let's proceed directly to the new state

        # order2 not filled
        if self.state == "order2" and self.order2.status == "closed" and self.order2.filled == 0:
            self.state = "finished"

            self.leg2_recovery_target = order2_best_recovery_start_amount(self.order1.filled_start_amount,
                                                                          self.order2.amount,
                                                                          self.order2.filled,
                                                                          self.recover_factor_order2)

            self.leg2_recovery_amount = self.order2.start_amount - self.order2.filled_start_amount

            self.finish_deal()
            return True

        # order3 create
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
                threshold_check_after_updates=50)

            if self.order2.filled < self.order2.amount*0.9999:
                self.leg2_recovery_target = order2_best_recovery_start_amount(self.order1.filled_start_amount,
                                                                              self.order2.amount,
                                                                              self.order2.filled,
                                                                              self.recover_factor_order2)
                self.leg2_recovery_amount = self.order2.start_amount - self.order2.filled_start_amount

            return True

        # order3 open
        if self.state == "order3_create" and (self.order3.status == "open" or self.order3.status == "closed"):
            self.state = "order3"
            # let's proceed directly to the new state

        # finished
        if self.state == "order3" and self.order3.status == "closed":
            self.state = "finished"

            if self.order3.filled < self.order3.amount * 0.9999:
                self.leg3_recovery_target = order3_best_recovery_start_amount(self.order1.filled_start_amount,
                                                                              self.order2.amount,
                                                                              self.order2.filled,
                                                                              self.order3.amount,
                                                                              self.order3.filled,
                                                                              self.recover_factor_order3)

                self.leg3_recovery_amount = self.order3.start_amount - self.order3.filled_start_amount

            self.finish_deal()

            return True

    def finish_deal(self):
        """
        calc all report parameters
        """

        self.filled_start_amount = self.order1.filled_start_amount
        self.result_amount = self.order3.filled_dest_amount if self.order3 is not None else 0.0
        self.gross_profit = self.result_amount - self.filled_start_amount

        if self.order1.filled == 0:
            self.status = "Failed"
            return

        if self.leg2_recovery_target > 0 or self.leg3_recovery_target > 0:
            self.status = "InRecovery"
            return

        if self.order1.filled > 0 and self.leg2_recovery_target == 0 and self.leg3_recovery_target == 0:
            self.status = "OK"
            return


class TriArbMakerCollection(object):
    """
    class to manage triarb deals collection raises exceptions on:
    - max_deals exceeded
    - adding deal with the existing uuid
    - when removing deal with unmatched uuid
    """

    def __init__(self, max_deals: int = 1):
        self.max_deals = max_deals
        self.deals = list()  # type: List[SingleTriArbMakerDeal]
        self.total_deals_added: int = 0
        self._deals_to_remove = list()
        """
        total numbers of deals added since start
        """

    def add_deal(self, deal: SingleTriArbMakerDeal):

        if deal.uuid == "":
            raise (Exception("Empty uuid"))

        if len(self.deals) == self.max_deals:
            raise (Exception("Max deals number {} exceeded".format(self.max_deals)))

        if next((index for (index, d) in enumerate(self.deals) if d.uuid == deal.uuid), None) is None:
            self.deals.append(deal)
            self.total_deals_added += 1
            return True
        else:
            raise(Exception("Deal with uuid {} is already exists".format(deal.uuid)))

    def remove_deal(self, uuid: str):
        deal_index = next((index for (index, d) in enumerate(self.deals) if d.uuid == uuid), None)
        if deal_index is not None:
            self.deals.pop(deal_index)
            return True

    def add_bulk_remove(self, uuid: str):
        deal = next((d for (index, d) in enumerate(self.deals) if d.uuid == uuid), None)

        if deal is not None:
            self._deals_to_remove.append(deal.uuid)
            return True

        raise (Exception("Deal with uuid {} not found".format(uuid)))

    def bulk_remove(self):
        deals_removed = list()

        self.deals = [deal for deal in self.deals if deal.uuid not in self._deals_to_remove]

        # for di in self._deals_to_remove:
        #     uuid = self.deals[di].uuid
        #     self.deals.pop(di)
        deals_removed = self._deals_to_remove
        self._deals_to_remove = list()
        return deals_removed

    def ok_to_add(self, new_deal: SingleTriArbMakerDeal):
        """
        will check if the deal is eligible to add the deal to deals' collection
        :param new_deal: deal to be added
        :return: str: OK is it's ok or reason if it's not ok
        """
        deals_count = 0

        for deal in self.deals:
            if new_deal.current_triangle == deal.current_triangle:
                deals_count += 1
                if deals_count > 1:
                    return "Too many deals with this triangle"

                # if deal.currency1 == new_deal.currency1 and deal.currency2 == new_deal.currency2:
                #     return "New deal with existing cur1 and cur2"

        return "OK"

