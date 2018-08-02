from .. import exchange_wrapper as ew
from  ..trade_orders import TradeOrder

class kucoin(ew.ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(kucoin, self).__init__(exchange_id, api_key, secret )
        self.wrapper_id = "kucoin"

    def _fetch_order(self, order):
        return self._ccxt.fetch_order(order.id, order.symbol, {"type": order.side.upper()})

    def _fetch_order_trades(self, order):

        resp = self._ccxt.fetch_order(order.id, order.symbol, {"type": order.side.upper()})
        if "trades" in resp and len(resp["trades"]) > 0:
            return resp["trades"]

        return list()

    @staticmethod
    def fees_from_order(order: TradeOrder):
        """
        returns the dict of cumulative fee as ["<CURRENCY>"]["amount"]

        :param order: TradeOrder
        :return:  the dict of cumulative fee as ["<CURRENCY>"]["amount"]
        """
        trades = order.trades
        total_fee = dict()

        for t in trades:
            t["fee"]["currency"] = order.dest_currency  # fee in dest currency

            if t["fee"]["currency"] not in total_fee:
                total_fee[t["fee"]["currency"]] = dict()
                total_fee[t["fee"]["currency"]]["amount"] = 0

            total_fee[t["fee"]["currency"]]["amount"] += t["fee"]["cost"]

        for c in order.start_currency, order.dest_currency:
            if c not in total_fee:
                total_fee[c] = dict({"amount": 0.0})

        return total_fee



    def get_exchange_wrapper_id(self):
        return self.wrapper_id
