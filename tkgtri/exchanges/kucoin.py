from .. import exchange_wrapper as ew
from  ..trade_orders import TradeOrder

class kucoin(ew.ccxtExchangeWrapper):

    def __init__(self, exchange_id, api_key ="", secret ="" ):
        super(kucoin, self).__init__(exchange_id, api_key, secret )
        self.wrapper_id = "kucoin"

    def _fetch_order(self, order):
        return self._ccxt.fetch_order(order.id, order.symbol, {"type": order.side.upper()})

    def _fetch_order_trades(self, order):
        resp = dict()
        amount_from_trades = 0
        if order.trades is not None and "amount" in order.trades:
            amount_from_trades = order.trades["amount"]

        if len(order.trades) <= 0 or (order.amount != amount_from_trades):
            resp = self._ccxt.fetch_order(order.id, order.symbol, {"type": order.side.upper()})
            amount_from_trades = resp["amount"]
        else:
            resp["trades"] = order.trades

        if len(resp["trades"]) > 0 and order.amount == amount_from_trades:
            # order.trades = resp["trades"]
            return resp["trades"]
        else:
            raise ew.ExchangeWrapperError("Amount in Trades is not matching Order Amount")

        return False

    @staticmethod
    def get_total_fees(order: TradeOrder):
        """
        returns the dict of cumulative fee as ["<CURRENCY>"]["amount"]

        :param order: TradeOrder
        :return:  the dict of cumulative fee as ["<CURRENCY>"]["amount"]
        """
        trades = order.trades
        total_fee = dict()

        for t in trades["trades"]:
            t["fee"]["currency"] = order.dest_currency  # fee in dest currency

            if t["fee"]["currency"] not in total_fee:
                total_fee[t["fee"]["currency"]] = dict()
                total_fee[t["fee"]["currency"]]["amount"] = 0

            total_fee[t["fee"]["currency"]]["amount"] += t["fee"]["cost"]

        for c in order.start_currency, order.dest_currency:
            if c not in total_fee:
                total_fee[c] = dict({"amount":0.0})

        return total_fee



    def get_exchange_wrapper_id(self):
        return self.wrapper_id
