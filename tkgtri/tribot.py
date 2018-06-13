import json
import logging
import sys
from . import utils
from . import timer

from .tri_cli import *
import tkgtri
from . import tri_arb as ta
import uuid
from .reporter import TkgReporter


class TriBot:

    def __init__(self, default_config, log_filename):

        self.session_uuid = str(uuid.uuid4())
        self.fetch_number = 0
        self.errors = 0

        self.config_filename = default_config
        self.exchange_id = str
        self.server_id = str
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

        self.timer = ...  # type: timer.Timer

        self.lap_time = float
        self.max_requests_per_lap = float
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

        self.influxdb = dict
        self.reporter = ...  # type: tkgtri.TkgReporter

        self.exchange = ...  # type: tkgtri.ccxtExchangeWrapper

        self.basic_triangles = list
        self.basic_triangles_count = int

        self.all_triangles = list

        self.markets = dict
        self.tickers = dict

        self.tri_list = list
        self.tri_list_good = list

        self.balance = float

        self.time = timer.Timer
        self.last_proceed_report = dict

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

    def init_reports(self, directory):

        self.deals_file_id = utils.get_next_report_filename(directory, self.report_deals_filename)

        self.report_deals_filename = self.report_deals_filename % (directory, self.deals_file_id)
        self.report_prev_tickers_filename = self.report_prev_tickers_filename % (directory, self.deals_file_id)
        self.report_dir = directory

    def init_remote_reports(self):
        self.reporter = TkgReporter(self.server_id, self.exchange_id)
        self.reporter.init_db(self.influxdb["host"], self.influxdb["port"], self.influxdb["db"],
                              self.influxdb["measurement"])

    def init_timer(self):
        self.timer = timer.Timer()
        self.timer.max_requests_per_lap = self.max_requests_per_lap
        self.timer.lap_time = self.lap_time

    def init_exchange(self):
        # exchange = getattr(ccxt, self.exchange_id)
        # self.exchange = exchange({'apiKey': self.api_key["apiKey"], 'secret': self.api_key["secret"] })
        # self.exchange.load_markets()

        self.exchange = tkgtri.ccxtExchangeWrapper.load_from_id(self.exchange_id, self.api_key["apiKey"],
                                                                self.api_key["secret"])

    def load_markets(self):
        self.markets = self.exchange.get_markets()

    def set_triangles(self):

        self.basic_triangles = ta.get_basic_triangles_from_markets(self.markets)
        self.all_triangles = ta.get_all_triangles(self.basic_triangles, self.start_currency)

        # return True

    def proceed_triangles(self):

        self.tri_list = ta.fill_triangles(self.all_triangles, self.start_currency, self.tickers, self.commission)

    def load_balance(self):
        if self.test_balance is not None:
            self.balance = self.test_balance

    def fetch_tickers(self):
        self.fetch_number += 1
        self.tickers = self.exchange.get_tickers()

    def get_good_triangles(self):
        # tri_list = list(filter(lambda x: x['result'] > 0, self.tri_list))
        tri_list = sorted(self.tri_list, key=lambda k: k['result'], reverse=True)

        threshold = self.threshold

        tri_list_good = list(
            filter(lambda x:
                   x['result'] is not None and x['result'] > threshold,
                   tri_list))

        self.tri_list_good = tri_list_good
        self.last_proceed_report = dict()
        self.last_proceed_report["best_result"] = tri_list[0]

        return len(tri_list_good)

    def get_status_report(self):

        report_fields = list("timestamp", "fetches", "good_triangles_total", "best_result", "best_triangle", "message")





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
