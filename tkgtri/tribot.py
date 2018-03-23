import importlib.util
import ccxt


class triBot:

    def __init__(self, start_currency: str, share_balance_to_bid: float, max_recovery_attempts: int, lot_limits: dict,
                 commission: float, threshold: float, threshold_orderbook: float, api_key: dict,
                 max_past_triangles: int, good_consecutive_results_threshold: int, lap_time: int,
                 max_transactions_per_lap: int):

        self.start_currency = start_currency
        self.share_balance_to_bid = share_balance_to_bid
        self.max_recovery_attempts = max_recovery_attempts
        self.lot_limits = lot_limits
        self.commission = commission
        self.threshold = threshold
        self.threshold_orderbook = threshold_orderbook
        self.api_key = api_key
        self.max_past_triangles = max_past_triangles
        self.good_consecutive_results_threshold = good_consecutive_results_threshold
        self.lap_time = lap_time
        self.max_transactions_per_lap = max_transactions_per_lap

    @classmethod
    def create_from_config(cls, config_file):
        name = "config"

        module_spec = importlib.util.spec_from_file_location(
            name, config_file)

        config = importlib.util.module_from_spec(module_spec)

        module_spec.loader.exec_module(config)

        return cls(config.start_cur, config.bal_share_to_bid, config.max_recovery_attempts, config.lot_limits,
                   config.commission, config.threshold, config.threshold_orderbook, config.api_key,
                   config.max_past_triangles,
                   config.good_consecutive_results_threshold, config.lap_time, config.max_transactions_per_lap)
