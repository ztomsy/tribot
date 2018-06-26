from tkgtri.trade_manager import *


# temp class for managing orders for old tribot
class OrderManagerFokLegacyBinance(OrderManagerFok):

    def create_order(self, exchange):
        return exchange.create_order(self.order.symbol, self.order.type, self.order.side, self.order.amount,
                                     self.order.price, {"newOrderRespType": "FULL"})

    def update_order(self, exchange):
        return exchange.fetch_order(self.order.id, self.order.symbol)