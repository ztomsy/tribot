import importlib.util
import ccxt
import json
import logging
import os
import sys
from .tri_cli import *


class TriBot:

    def __init__(self, default_config, log_filename):

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

        self.tickers_file = str

        self.log_filename = log_filename

        self.logger = self.init_logging(self.log_filename)

        self.LOG_DEBUG = logging.DEBUG
        self.LOG_INFO = logging.INFO
        self.LOG_ERROR = logging.ERROR
        self.LOG_CRITICAL = logging.CRITICAL

    # load config from json
    def load_config_from_file(self, config_file):

        with open(config_file) as json_data_file:
            cnf = json.load(json_data_file)

        for i in cnf :
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


    def log(self, level, msg):

        self.logger.log(level, msg)

    #
    # get next filename under the [exchange directory]. if there is no folder for filename - the folder will be created
    #
    def get_next_report_filename(self, filename):

        filename = "_"+self.exchange_id+"/"+filename
        directory = os.path.dirname(filename)

        try:
            os.stat(directory)

        except:
            os.mkdir(directory)
            print("New directory created:", directory)

        deals_id = 0
        while os.path.exists(filename % deals_id):
            deals_id += 1

        return deals_id

    def print_logo(self, product = ""):
        print('TTTTTTTTTT    K    K     GGGGG')
        print('    T         K   K     G')
        print('    T         KKKK      G')
        print('    T         K  K      G  GG')
        print('    T         K   K     G    G')
        print('    T         K    K     GGGGG')
        print('-' * 36)
        print('          %s               ' % product)
        print('-' * 36)