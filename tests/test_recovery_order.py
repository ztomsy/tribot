from .context import tkgtri
from tkgtri import RecoveryOrder
import unittest
import copy


class OrderWithAimTestSuite(unittest.TestCase):

    def test_comparison_eq(self):
        rm1 = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)
        rm2 = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)

        self.assertEqual(rm1, rm1)
        self.assertNotEqual(rm1, rm2)

        rm2.id = rm1.id
        self.assertEqual(rm1, rm1)

        rm2 = copy.copy(rm1)
        self.assertEqual(rm1, rm2)

        rm2.status = "closed"
        self.assertNotEqual(rm1, rm2)

        rm2 = copy.copy(rm1)
        rm2.filled = 1
        self.assertNotEqual(rm1, rm2)


class RecoveryOrderTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_amount_for_best_dest_price(self):
        rm = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)
        price = rm.get_recovery_price_for_best_dest_amount()
        self.assertAlmostEqual(price, 0.00032485, 8)

    def test_create_trade_order(self):
        rm = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)
        order = rm.create_recovery_order(rm.get_recovery_price_for_best_dest_amount())

        self.assertEqual(order.dest_currency, "ETH")
        self.assertEqual(order.amount, 1000)
        self.assertEqual(order.side, "sell")

        self.assertEqual(rm.amount, 1000)

    def test_update_from_exchange(self):
        ro = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)

        # update 1 - partial fill
        resp = {"status":"open", "filled": 500, "cost": 0.32485131/2}
        ro.update_from_exchange(resp)
        self.assertEqual(ro.filled_start_amount, 500)
        self.assertEqual(ro.filled, 500)
        self.assertEqual(ro.status, "open")
        self.assertEqual(ro.state, "best_amount")
        self.assertEqual(ro.order_command, "hold")
        self.assertEqual(ro.filled_price, ro.active_order.price)

    def test_fill_best_amount(self):

        ro = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)

        # update 1 - partial fill
        resp = {"status":"open", "filled": 500, "cost": 0.32485131/2}
        ro.update_from_exchange(resp)
        self.assertEqual(ro.filled_start_amount, 500)
        self.assertEqual(ro.filled, 500)
        self.assertEqual(ro.status, "open")
        self.assertEqual(ro.state, "best_amount")
        self.assertEqual(ro.order_command, "hold")
        self.assertEqual(ro.filled_price, ro.active_order.price)

        # update 2 - complete fill
        resp = {"status": "closed", "filled": 1000, "cost": 0.32485131}
        ro.update_from_exchange(resp)
        self.assertEqual(ro.filled_start_amount, 1000)
        self.assertEqual(ro.filled, 1000)
        self.assertEqual(ro.status, "closed")
        self.assertEqual(ro.order_command, "")
        self.assertEqual(ro.state, "best_amount")

    def test_fill_market_price_from_1st_order(self):

        ro = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)

        # updates max_updates -1 : order should be partially filled
        for i in range(1, ro.max_order_updates):
            resp = {"status": "open", "filled": 500, "cost": 0.32485131/2}
            ro.update_from_exchange(resp)
            self.assertEqual(ro.filled_start_amount, 500)
            self.assertEqual(ro.filled, 500)
            self.assertEqual(ro.status, "open")
            self.assertEqual(ro.state, "best_amount")
            self.assertEqual(ro.order_command, "hold")

        # last order update before the cancelling active trade order
        resp = {"status": "open", "filled": 500, "cost": 0.32485131 / 2}
        ro.update_from_exchange(resp)
        self.assertEqual(ro.order_command, "cancel")

        # active trade order is cancelled - the command for the new order
        ro.update_from_exchange({"status": "canceled"}, {"price": 1})
        self.assertEqual(ro.order_command, "new")

        # parameters of new order: market price and amount of start curr which left to fill
        self.assertEqual(ro.active_order.price, 1)
        self.assertEqual(ro.active_order.amount, 500)

        self.assertEqual(ro.filled_start_amount, 500)
        self.assertEqual(ro.filled_dest_amount, 0.32485131/2)
        self.assertEqual(ro.filled, 500)
        self.assertEqual(len(ro.orders_history), 1)
        self.assertEqual(ro.orders_history[0].status, "canceled")

        # new order created and started to fill
        ro.update_from_exchange({"status": "open", "filled": 100})
        self.assertEqual(ro.filled, 600)
        self.assertEqual(ro.state, "market_price")
        self.assertEqual(ro.status, "open")
        self.assertEqual(ro.active_order.status, "open")
        self.assertEqual(ro.active_order.filled, 100)

        ro.update_from_exchange({"status": "open", "filled": 200})
        self.assertEqual(ro.active_order.filled, 200)
        self.assertEqual(ro.filled, 700)

        ro.update_from_exchange({"status": "closed", "filled": 500})
        self.assertEqual(ro.active_order, None)
        self.assertEqual(ro.orders_history[1].filled, 500)

        self.assertEqual(ro.filled, 1000)
        self.assertEqual(ro.status, "closed")
        self.assertEqual(ro.state, "market_price")
        self.assertEqual(ro.order_command, "")

    def test_fill_market_price_6_orders(self):

        ro = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)

        # best_amount filled with zero result
        for i in range(1, ro.max_order_updates+1):
            resp = {"status": "open", "filled": 0, "cost": 0}
            ro.update_from_exchange(resp)
        self.assertEqual(ro.filled, 0)
        self.assertEqual(ro.status, "open")
        self.assertEqual(ro.state, "best_amount")
        self.assertEqual(ro.order_command, "cancel")

        ro.update_from_exchange({"status": "canceled", "filled": 500}, {"price": 1})
        self.assertEqual(ro.order_command, "new")

        for i in range(1, 5):  # i  will be from 1 to 4 - 4 orders in total
            ro.update_from_exchange({"status": "open", "filled": 0}, {"price": 1})

            self.assertEqual(ro.state, "market_price")
            self.assertEqual(ro.order_command, "hold")
            self.assertEqual(len(ro.orders_history), i)
            self.assertEqual(ro.filled, sum(item.filled for item in ro.orders_history))

            for j in range(1, ro.max_order_updates):
                ro.update_from_exchange({"status": "open", "filled": 10}, {"price": 1})

            ro.update_from_exchange({"status": "open", "filled": 100}, {"price": 1})
            self.assertEqual(ro.order_command, "cancel")

            ro.update_from_exchange({"status": "canceled", "filled": 100}, {"price": 1})

        self.assertEqual(ro.order_command, "new")  # 6th order
        ro.update_from_exchange({"status": "closed", "filled": 100}, {"price": 1})
        self.assertEqual(ro.filled, 1000)

    def test_1st_order_executed_better(self):
        pass

    def test_2nd_order_executed_better(self):
        pass

if __name__ == '__main__':
    unittest.main()

