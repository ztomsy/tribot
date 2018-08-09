from tkgtri import core
from tkgtri import TradeOrder
from tkgtri import ccxtExchangeWrapper
from datetime import datetime


class RecoveryManager(object):

    def __init__(self, start_currency: str, start_amount: float, dest_currency: str,
                 best_dest_amount: float = 0.0,
                 fee: float = 0.0,
                 exchange: ccxtExchangeWrapper = None):

        self.start_currency = start_currency
        self.start_amount = start_amount
        self.dest_currency = dest_currency
        self.fee = fee
        self.best_dest_amount = best_dest_amount

        self.exchange = exchange

        self.best_price = 0.0

        if exchange is not None:
            self.symbol = core.get_symbol(start_currency, dest_currency, exchange.markets)

        self.side = core.get_trade_direction_to_currency(dest_currency, self.symbol) if self.symbol else None

    def get_recovery_price_for_best_amount(self):
        """
        :return: price for recovery order from target_amount and target_currency without fee
        """
        if self.side == "buy":
            return self.best_dest_amount / self.start_amount

        if self.side == "sell":
            return self.start_amount / self.best_dest_amount

        return False

    def create_recovery_order(self):
        pass

