from .context import tkgtri
from tkgtri import RecoveryOrder
import unittest
import json


class RecoveryOrderTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_amount_for_best_dest_price(self):
        rm = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)
        price = rm.get_recovery_price_for_best_dest_amount()
        self.assertAlmostEqual(price, 0.00032485, 8)

    def test_create_order(self):
        rm = RecoveryOrder("ADA/ETH", "ADA", 1000, "ETH", 0.32485131)
        order = rm.create_recovery_order(rm.get_recovery_price_for_best_dest_amount())

        self.assertEqual(order.dest_currency, "ETH")
        self.assertEqual(order.amount, 1000)
        self.assertEqual(order.side, "sell")


if __name__ == '__main__':
    unittest.main()

