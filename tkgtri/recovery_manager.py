from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
from datetime import datetime


class RecoveryManager(object):

    def __init__(self, order: TradeOrder, target_currency: str, target_amount: float):

        self.order = order
        self.target_currency = target_currency
        self.target_amount = target_amount

    def get_recovery_price(self):
        """
        :return: price for recovery order from target_amount and target_currency
        """
        pass

    def create_recovery_order(self):
        pass

