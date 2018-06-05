import importlib.util
import ccxt
import json
import logging
import os
import sys
from . import utils
from . import timer

from .tri_cli import *
import networkx as nx
import numpy as np
import tkgtri
from . import tri_arb as ta

class TriBot:

    def __init__(self, default_config, log_filename):

        self.config_filename = default_config
        self.exchange_id = str
        self.server = str
        self.script_id = str
        self.start_currency = list
        self.share_balance_to_bid = float
        self.max_recovery_attempts = int
        self.lot_limits = dict
        self.commission = float
        self.threshold = float
        self.threshold_order_book = float
        self.balance_bid_thresholds = dict
        self.api_key = dict
        self.max_past_triangles = int
        self.good_consecutive_results_threshold = int
        self.lap_time = float
        self.max_transactions_per_lap = float
        self.test_balance = float

        self.live = bool
        self.debug = bool

        self.tickers_file = str

        self.logger = logging
        self.log_filename = log_filename

        self.logger = self.init_logging(self.log_filename)

        self.LOG_DEBUG = logging.DEBUG
        self.LOG_INFO = logging.INFO
        self.LOG_ERROR = logging.ERROR
        self.LOG_CRITICAL = logging.CRITICAL

        self.report_all_deals_filename = str
        self.report_tickers_filename = str
        self.report_deals_filename = str
        self.report_prev_tickers_filename = str

        self.report_dir = str
        self.deals_file_id = int

        #self.exchange = None

        self.exchange = ...  # type: tkgtri.ccxtExchangeWrapper

        self.basic_triangles = list
        self.basic_triangles_count = int

        self.all_triangles = list

        self.markets = dict
        self.tickers = dict

        self.tri_list = list

        self.balance = float

        self.time = timer.Timer


        # load config from json

    def load_config_from_file(self, config_file):

        with open(config_file) as json_data_file:
            cnf = json.load(json_data_file)

        for i in cnf:
            attr_val = cnf[i]
            if type(getattr(self, i)) == type and attr_val is not None:
                setattr(self, i, attr_val)

    # parse cli
    def set_from_cli(self, args):

        cli_args = get_cli_parameters(args)

        for i in cli_args.__dict__:
            attr_val = getattr(cli_args, i)
            if attr_val is not None:
                setattr(self, i, attr_val)

    #
    # init logging
    #

    def init_logging(self, file_log):

        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        logger = logging.getLogger()

        file_handler = logging.FileHandler(file_log)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

        logger.setLevel(logging.INFO)

        return logger

    def set_log_level(self, log_level):

        self.logger.setLevel(log_level)

    def log(self, level, msg, msg_list=None):
        if msg_list is None:
            self.logger.log(level, msg)
        else:
            self.logger.log(level, msg)
            for line in msg_list:
                self.logger.log(level, "... " + line)

    def init_reports(self, dir):

        self.deals_file_id = utils.get_next_report_filename(dir, self.report_deals_filename)

        self.report_deals_filename = self.report_deals_filename % (dir, self.deals_file_id)
        self.report_prev_tickers_filename = self.report_prev_tickers_filename % (dir, self.deals_file_id)
        self.report_dir = dir

    def init_timer(self):
        self.timer = timer.Timer()
        self.timer.max_transactions_per_lap = self.max_transactions_per_lap
        self.timer.lap_time = self.lap_time

    def init_exchange(self):
        # exchange = getattr(ccxt, self.exchange_id)
        # self.exchange = exchange({'apiKey': self.api_key["apiKey"], 'secret': self.api_key["secret"] })
        # self.exchange.load_markets()

        self.exchange = tkgtri.ccxtExchangeWrapper.load_from_id(self.exchange_id, self.api_key["apiKey"], self.api_key["secret"])

    def load_markets(self):
        self.markets = self.exchange.get_markets()

    def set_triangles(self):

        self.basic_triangles = ta.get_basic_triangles_from_markets(self.markets)
        self.all_triangles = ta.get_all_triangles(self.basic_triangles, self.start_currency)


        #return True

    def proceed_triangles(self):

        self.tri_list = ta.fill_triangles(self.all_triangles, self.start_currency, self.tickers, self.commission)


    def load_balance(self):
        if self.test_balance is not None:
            self.balance = self.test_balance

    def fetch_tickers(self):
        self.tickers = self.exchange.get_tickers()



    @staticmethod
    def print_logo(product=""):
        print('TTTTTTTTTT    K    K     GGGGG')
        print('    T         K   K     G')
        print('    T         KKKK      G')
        print('    T         K  K      G  GG')
        print('    T         K   K     G    G')
        print('    T         K    K     GGGGG')
        print('-' * 36)
        print('          %s               ' % product)
        print('-' * 36)
