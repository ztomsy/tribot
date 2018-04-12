import importlib.util
import ccxt
import json
from .tri_cli import *


class TriBot:

    def __init__(self, default_config):

        self.config_filename = default_config
        self.exchange_id = str
        self.server = str
        self.start_currency = str
        self.share_balance_to_bid = float
        self.max_recovery_attempts = int
        self.lot_limits = dict
        self.commission = float
        self.threshold = float
        self.threshold_order_book = float
        self.api_key = dict
        self.max_past_triangles = int
        self.good_consecutive_results_threshold = int
        self.lap_time = float
        self.max_transactions_per_lap = float
        self.test_balance = float

        self.live = bool
        self.debug = bool

    # load config from json
    def load_config_from_file(self, config_file):

        with open(config_file) as json_data_file:
            cnf = json.load(json_data_file)

        for i in cnf :
            attr_val = cnf[i]
            if type(getattr(self, i)) == type and attr_val is not None:
                setattr(self, i, attr_val)

        # self.exchange_id = cnf["exchange_id"]
        # self.server = cnf["server"]
        # self.start_currency = cnf["start_currency"]
        # self.share_balance_to_bid = cnf["share_balance_to_bid"]
        # self.max_recovery_attempts = cnf["max_recovery_attempts"]
        # self.lot_limits = cnf["lot_limits"]
        # self.commission = cnf["commission"]
        # self.threshold = cnf["threshold"]
        # self.threshold_orderbook = cnf["threshold_orderbook"]
        # self.api_key = cnf["api_key"]
        # self.max_past_triangles = cnf["max_past_triangles"]
        # self.good_consecutive_results_threshold = cnf["good_consecutive_results_threshold"]
        # self.lap_time = cnf["lap_time"]
        # self.max_transactions_per_lap = cnf["max_transactions_per_lap"]

    # parse cli
    def set_from_cli(self, args):

        cli_args = get_cli_parameters(args)

        for i in cli_args.__dict__:
            attr_val = getattr(cli_args, i)
            if attr_val is not None:
                setattr(self, i, attr_val)

        # self.nolive = cli_args.nolive
        # self.nodebug = cli_args.nodebug
        # self.exchange_id = cli_args.exchange
        # self.fake_balance = cli_args.balance


    # @classmethod
    # def create_from_config(cls, config_file):
    #
    #     bot = cls(config_file)
    #
    #     config_parameters = cls.load_config_from_file(config_file)
    #
    #
    #
    #
    #     return cls(config.start_cur, config.bal_share_to_bid, config.max_recovery_attempts, config.lot_limits,
    #                config.commission, config.threshold, config.threshold_orderbook, config.api_key,
    #                config.max_past_triangles,
    #                config.good_consecutive_results_threshold, config.lap_time, config.max_transactions_per_lap)


