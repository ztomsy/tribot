from tkgtri.trade_manager import *


# temp class for managing orders for old tribot
class OrderManagerFokLegacyBinance(OrderManagerFok):

    def create_order(self, exchange):
        return exchange.create_order(self.order.symbol, self.order.type, self.order.side, self.order.amount,
                                     self.order.price, {"newOrderRespType": "FULL"})

    def update_order(self, exchange):
        return exchange.fetch_order(self.order.id, self.order.symbol)

    def cancel_order(self, exchange):
        return exchange.cancel_order(self.order.id, self.order.symbol)

    def emulate_order(self):
        binance_order = dict()

        executed_qty = self.order.amount_dest if self.order.side == "sell" else self.order.amount_start

        binance_order = {
            "cost": 0.012017544,
            "datetime": "2018-06-27T09:19:12.350Z",
            "side": "sell",
            "timestamp": 1530091152350,
            "info": {
                "clientOrderId": "msRgafgtCe56bVhZTMajTc",
                "timeInForce": "GTC",
                "orderId": 172438836,
                "executedQty": executed_qty,
                "side": "SELL",
                "symbol": "ETHBTC",
                "status": "FILLED",
                "price": str(self.order.price),
                "transactTime": 1530091152350,
                "type": "LIMIT",
                "origQty": "0.70000000"
            },
            "symbol": "ETH/BTC",
            "status": "closed",
            "fee": None,
            "amount": self.order.amount,
            "filled": self.order.amount,
            "price": self.order.price,
            "remaining": 0,
            "id": "172438836",
            "type": "limit",
            "lastTradeTimestamp": None
        }
