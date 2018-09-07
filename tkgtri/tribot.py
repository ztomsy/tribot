import json
import logging
import sys
from . import utils
from . import timer
from .tri_cli import *
import tkgtri
from . import tri_arb as ta
import uuid
import copy
from .reporter import TkgReporter
import bisect
import datetime
import time
from .trade_orders import *
from .trade_manager import *
from . import rest_server
import collections


class TriBot:

    def __init__(self, default_config: str, log_filename=None):

        self.session_uuid = str(uuid.uuid4())
        self.fetch_number = 0
        self.errors = 0

        self.config_filename = default_config
        self.exchange_id = ""
        self.server_id = ""
        self.script_id = ""
        self.start_currency = list()
        self.share_balance_to_bid = float()
        self.max_recovery_attempts = int()
        self.min_amounts = dict()
        self.commission = float()
        self.threshold = float()
        self.threshold_order_book = float()
        self.balance_bid_thresholds = dict()
        self.api_key = dict()
        self.max_past_triangles = int()
        self.good_consecutive_results_threshold = int()

        self.max_trades_updates = 10

        self.order_update_requests_for_time_out = 0.0
        self.order_update_time_out = 1

        self.timer = ...  # type: timer.Timer

        self.lap_time = float()
        self.max_requests_per_lap = 0.0

        self.test_balance = float()
        self.force_start_amount = float()

        self.force_best_tri = bool()
        self.debug = bool()
        self.run_once = False
        self.noauth = False
        self.offline = False

        self.recovery_server = ""

        self.tickers_file = str()

        self.logger = logging
        self.log_filename = log_filename

        self.logger = self.init_logging(self.log_filename)

        self.LOG_DEBUG = logging.DEBUG
        self.LOG_INFO = logging.INFO
        self.LOG_ERROR = logging.ERROR
        self.LOG_CRITICAL = logging.CRITICAL

        self.report_all_deals_filename = str()
        self.report_tickers_filename = str()
        self.report_deals_filename = str()
        self.report_prev_tickers_filename = str()

        self.report_dir = str()
        self.deals_file_id = int()

        self.influxdb = dict()
        self.reporter = ...  # type: tkgtri.TkgReporter

        self.exchange = ...  # type: tkgtri.ccxtExchangeWrapper

        self.basic_triangles = list()
        self.basic_triangles_count = int()

        self.all_triangles = list()

        self.markets = dict()
        self.tickers = dict()

        self.tri_list = list()
        self.tri_list_good = list()

        # self.recovery_data = list()

        self.balance = float()

        self.time = timer.Timer
        self.last_proceed_report = dict()

        # load config from json

    def load_config_from_file(self, config_file):

        with open(config_file) as json_data_file:
            cnf = json.load(json_data_file)

        for i in cnf:
            attr_val = cnf[i]
            if not bool(getattr(self, i)) and attr_val is not None:
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

    def init_logging(self, file_log=None):

        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        logger = logging.getLogger()

        if file_log is not None:
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
                self.logger.log(level, "... " + str(line))

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
        if not self.noauth:
            self.exchange = tkgtri.ccxtExchangeWrapper.load_from_id(self.exchange_id, self.api_key["apiKey"],
                                                                    self.api_key["secret"])
        else:
            self.exchange = tkgtri.ccxtExchangeWrapper.load_from_id(self.exchange_id)

    def load_markets(self):
        self.markets = self.exchange.get_markets()

    def set_triangles(self):

        self.basic_triangles = ta.get_basic_triangles_from_markets(self.markets)
        self.all_triangles = ta.get_all_triangles(self.basic_triangles, self.start_currency)

        # return True

    def proceed_triangles(self):

        self.tri_list = ta.fill_triangles(self.all_triangles, self.start_currency, self.tickers, self.commission)

    def load_balance(self):

        if self.test_balance > 0:
            self.balance = self.test_balance
            return self.test_balance
        else:
            self.balance = self.exchange.fetch_free_balance()[self.start_currency[0]] if not self.offline else 0.0
            return self.balance

    #
    # get maximum balance to bid in respect to thresholds set in config
    #
    def get_max_balance_to_bid(self, currency=None, balance=None, result=None, ob_result=None):

        currency = self.start_currency[0] if currency is None else currency
        balance = self.balance if balance is None else balance
        result = self.tri_list_good[0]["result"] if result is None else result
        ob_result = self.tri_list_good[0]["ob_result"] if ob_result is None else ob_result

        # balance_results_thresholds_config = self.balance_bid_thresholds[currency]

        balance_results_thresholds_config = dict()

        for l in self.balance_bid_thresholds[currency]:
            balance_results_thresholds_config[float(l["max_bid"])] = l

        balance_thresholds = sorted(list(balance_results_thresholds_config.keys()))

        try:
            i = bisect.bisect_left(balance_thresholds, balance)
        except IndexError:
            i = 0

        if i >= len(balance_thresholds):
            i = len(balance_thresholds) - 1

        while i >= 0:
            if result >= balance_results_thresholds_config[balance_thresholds[i]]['result_threshold'] and \
                    ob_result >= balance_results_thresholds_config[balance_thresholds[i]]["orderbook_result_threshold"]:
                to_bid = min(balance, balance_thresholds[i])
                return to_bid

            else:
                i = i - 1
        return None

    def get_order_books_async(self, symbols: list):
        """
        returns the dict of {"symbol": OrderBook} in offline mode the order book is single line - ticker price and big
         amount
        :param symbols: list of symbols to get orderbooks
        :return: returns the dict of {"symbol": OrderBook}
        """

        ob_array = self.exchange.get_order_books_async(symbols)
        order_books = dict()
        for ob in ob_array:
            order_books[ob["symbol"]] = tkgtri.OrderBook(ob["symbol"], ob["asks"], ob["bids"])

        return order_books

    def fetch_tickers(self):
        self.fetch_number += 1
        self.tickers = self.exchange.get_tickers()

    def get_good_triangles(self):
        """

        :return: sorted by result list of good triangles
        """
        # tri_list = list(filter(lambda x: x['result'] > 0, self.tri_list))
        self.tri_list = sorted(self.tri_list, key=lambda k: k['result'], reverse=True)

        threshold = self.threshold

        tri_list_good = list(
            filter(lambda x:
                   x['result'] is not None and x['result'] > threshold,
                   self.tri_list))

        # self.tri_list_good = tri_list_good
        self.last_proceed_report = dict()
        self.last_proceed_report["best_result"] = self.tri_list[0]

        return tri_list_good

    def log_order_create(self, order_manager: tkgtri.OrderManagerFok):
        self.log(self.LOG_INFO, "Tick {}: Order {} created. Filled dest curr:{} / {} ".format(
            order_manager.order.update_requests_count,
            order_manager.order.id,
            order_manager.order.filled_dest_amount,
            order_manager.order.amount_dest))

    # here is the sleep between updates is implemented! needed to be fixed
    def log_order_update(self, order_manager: tkgtri.OrderManagerFok):
        self.log(self.LOG_INFO, "Order {} update req# {}/{} (to timer {}). Status:{}. Filled amount:{} / {} ".format(
            order_manager.order.id,
            order_manager.order.update_requests_count,
            order_manager.updates_to_kill,
            self.order_update_requests_for_time_out,
            order_manager.order.status,
            order_manager.order.filled,
            order_manager.order.amount))

        now_order = datetime.now()

        if order_manager.order.status == "open" and \
                order_manager.order.update_requests_count >= self.order_update_requests_for_time_out:

            if order_manager.order.update_requests_count >= order_manager.updates_to_kill:
                self.log(self.LOG_INFO, "...last update will no sleep")

            else:
                self.log(self.LOG_INFO, "...reached the number of order updates for timeout")

                if (now_order - order_manager.last_update_time).total_seconds() < self.order_update_time_out:
                    self.log(self.LOG_INFO, "...sleeping while order update for {}".format(self.order_update_time_out))
                    time.sleep(self.order_update_time_out)

                order_manager.last_update_time = datetime.now()

    def log_on_order_update_error(self, order_manager, exception):
        self.log(self.LOG_ERROR, "Error updating  order_id: {}".format(order_manager.order.id))
        self.log(self.LOG_ERROR, "Exception: {}".format(type(exception).__name__))

        for ll in exception.args:
            self.log(self.LOG_ERROR, type(exception).__name__ + ll)

        return True

    def assign_updates_functions_for_order_manager(self):
        OrderManagerFok.on_order_create = lambda _order_manager: self.log_order_create(_order_manager)
        OrderManagerFok.on_order_update = lambda _order_manager: self.log_order_update(_order_manager)
        OrderManagerFok.on_order_update_error = lambda _order_manager, _exception: self.log_on_order_update_error(
            _order_manager, _exception)

    def do_trade(self, symbol, start_currency, dest_currency, amount, side, price):

        order = TradeOrder.create_limit_order_from_start_amount(symbol, start_currency, amount, dest_currency, price)

        if self.offline:
            o = self.exchange.create_order_offline_data(order, 3)
            self.exchange._offline_order = copy.copy(o)
            self.exchange._offline_trades = copy.copy(o["trades"])
            self.exchange._offline_order_update_index = 0
            self.exchange._offline_order_cancelled = False

        order_manager = OrderManagerFok(order, None, updates_to_kill=5)

        try:
            order_manager.fill_order(self.exchange)
        except OrderManagerErrorUnFilled:
            try:
                self.log(self.LOG_INFO, "Cancelling order...")
                order_manager.cancel_order(self.exchange)

            except OrderManagerCancelAttemptsExceeded:
                self.log(self.LOG_ERROR, "Could not cancel order")
                self.errors += 1

        except Exception as e:
            self.log(self.LOG_ERROR, "Order error")
            self.log(self.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            self.log(self.LOG_ERROR, "Exception body:", e.args)
            self.log(self.LOG_ERROR, order.info)

            self.errors += 1
        return order

    def get_trade_results(self, order: TradeOrder):

        results = list()
        i = 0
        while bool(results) is not True and i < self.max_trades_updates:
            self.log(self.LOG_INFO, "getting trades #{}".format(i))
            try:
                results = self.exchange.get_trades_results(order)
            except Exception as e:
                self.log(self.LOG_ERROR, type(e).__name__)
                self.log(self.LOG_ERROR, e.args)
                self.log(self.LOG_INFO, "retrying to get trades...")
            i += 1

        return results

    @staticmethod
    def order2_best_recovery_start_amount(filled_start_currency_amount, order2_amount, order2_filled):

        res = filled_start_currency_amount - (order2_filled / order2_amount) * filled_start_currency_amount
        return res

    @staticmethod
    def order3_best_recovery_start_amount(filled_start_currency_amount, order2_amount, order2_filled, order3_amoumt,
                                          order3_filled):

        res = filled_start_currency_amount * (order2_filled / order2_amount) * (1 - (order3_filled / order3_amoumt))

        return res

    def create_recovery_data(self, deal_uuid, start_cur: str, dest_cur: str, start_amount: float,
                             best_dest_amount: float, leg: int) -> dict:
        recovery_dict = dict()
        recovery_dict["deal_uuid"] = deal_uuid
        recovery_dict["symbol"] = core.get_symbol(start_cur, dest_cur, self.markets)
        recovery_dict["start_cur"] = start_cur
        recovery_dict["dest_cur"] = dest_cur
        recovery_dict["start_amount"] = start_amount
        recovery_dict["best_dest_amount"] = best_dest_amount
        recovery_dict["leg"] = leg  # order leg to recover from
        recovery_dict["timestamp"] = time.time()

        return recovery_dict

    def print_recovery_data(self, recovery_data):
        self.log(self.LOG_INFO, "leg {}".format(recovery_data["leg"]))
        self.log(self.LOG_INFO, "Recover leg {}: {} {} -> {} {} ".
                 format(recovery_data["leg"], recovery_data["start_cur"], recovery_data["start_amount"],
                        recovery_data["dest_cur"], recovery_data["best_dest_amount"]))

    def send_recovery_request(self, recovery_data: dict):
        self.log(self.LOG_INFO, "Sending recovery request...")
        try:

            resp = rest_server.rest_call_json(
                "{}:{}/order/".format(self.recovery_server["host"], self.recovery_server["port"]),
                recovery_data, "PUT")

        except Exception as e:
            self.log(self.LOG_ERROR, "Could not send recovery request")
            self.log(self.LOG_ERROR, "Exception: {}".format(type(e).__name__))
            self.log(self.LOG_ERROR, "Exception body:", e.args)
            return False

        self.log(self.LOG_INFO, "Response: {}".format(resp))
        return resp

    @staticmethod
    def get_report_fields():
        return list([
            "server-id", "exchange-id", "session-uuid", "fetch-number", "deal-uuid", "dbg", "triangle", "status",
            "start-qty", "start-filled", "finish-qty", "result-fact-diff", "for-recover",
            "leg2-recover-amount", "leg2-recover-target", "leg3-recover-amount", "leg3-recover-target",
            "result", "ob_result",
            "leg1-order-result", "leg1-filled", "leg1-price-fact", "leg1-ob-price", "leg1-price", "leg1-fee",
            "leg2-order-result", "leg2-filled", "leg2-price-fact", "leg2-ob-price", "leg2-price", "leg2-fee",
            "leg3-order-result", "leg3-filled", "leg3-price-fact", "leg3-ob-price", "leg3-price", "leg3-fee",
            "leg1-order-updates", "leg2-order-updates", "leg3-order-updates",
            "cur1", "cur2", "cur3", "leg1-order", 'leg2-order', 'leg3-order', 'symbol1', 'symbol2', 'symbol3',
            "time_fetch", "time_proceed", "time_from_start", "errors", "time_after_deals"])

    def get_deal_report(self, working_triangle: dict, recovery_data, order1: TradeOrder, order2: TradeOrder = None,
                        order3: TradeOrder = None, price1=None, price2=None, price3=None):

        report_fields = self.get_report_fields()

        report = dict()

        wt = copy.copy(working_triangle)

        # adding report data which are not in working triangle
        wt["server-id"] = self.server_id
        wt["exchange-id"] = self.exchange_id
        wt["dbg"] = self.debug
        wt["live"] = self.force_best_tri
        wt["session-uuid"] = self.session_uuid
        wt["errors"] = self.errors
        wt["fetch_number"] = self.fetch_number

        wt["start-qty"] = order1.amount_start if order1 is not None else None
        wt["start-filled"] = order1.filled_start_amount if order1 is not None else None

        wt["status"] = "InRecovery" if len(recovery_data) > 0 else working_triangle["status"]

        wt["leg1-order-status"] = order1.status if order1 is not None else None
        wt["leg2-order-status"] = order2.status if order2 is not None else None
        wt["leg3-order-status"] = order3.status if order3 is not None else None

        wt["leg1-filled"] = order1.filled / order1.amount if order1 is not None and order1.amount != 0 else 0.0
        wt["leg2-filled"] = order2.filled / order2.amount if order2 is not None and order2.amount != 0 else 0.0
        wt["leg3-filled"] = order3.filled / order3.amount if order3 is not None and order3.amount != 0 else 0.0

        wt["leg1-order-updates"] = order1.update_requests_count if order1 is not None else None
        wt["leg2-order-updates"] = order2.update_requests_count if order2 is not None else None
        wt["leg3-order-updates"] = order3.update_requests_count if order3 is not None else None

        wt["leg1-price-fact"] = order1.cost / order1.filled if order1 is not None and order1.filled != 0 else 0.0
        wt["leg2-price-fact"] = order2.cost / order2.filled if order2 is not None and order2.filled != 0 else 0.0
        wt["leg3-price-fact"] = order3.cost / order3.filled if order3 is not None and order3.filled != 0 else 0.0

        wt["leg1-ob-price"] = price1
        wt["leg2-ob-price"] = price2
        wt["leg3-ob-price"] = price3

        wt["leg1-fee"], wt["leg2-fee"], wt["leg3-fee"] = (order.fees[order.dest_currency]["amount"]
                                                          if order is not None and order.dest_currency in order.fees
                                                          else None
                                                          for order in (order1, order2, order3))

        if order3 is not None and order1 is not None:
            wt["finish-qty"] = order3.filled_dest_amount - order3.fees[order3.dest_currency]["amount"]
            wt["result-fact-diff"] = float(wt["finish-qty"] - order1.filled_start_amount)
            wt["result-fact"] = order3.filled_dest_amount / order1.filled_start_amount
        else:
            wt["result-fact-diff"] = 0.0

        total_recover_amount = float(0.0)

        # collect recovery data
        for r in recovery_data:
            total_recover_amount += r["best_dest_amount"]
            wt["leg{}-recover-amount".format(r["leg"])] = r["start_amount"]  # amount of CUR in leg sent to recover
            wt["leg{}-recover-target".format(r["leg"])] = r["best_dest_amount"]  # amount of target CUR1 for recover
        wt["for-recover"] = total_recover_amount

        # collect timer data
        time_report = self.timer.results_dict()

        for f in time_report:
            report_fields.append(f)
            wt[f] = time_report[f]

        # copy working triangle data into report
        for f in report_fields:
            if f in wt:
                report[f] = wt[f]

        return report

    def log_report(self, report):
        for r in self.get_report_fields():
            self.log(self.LOG_INFO, "{} = {}".format(r, report[r] if r in report else "None"))

    def send_remote_report(self, report):
        for r in report:
            self.reporter.set_indicator(r, report[r])

        self.reporter.push_to_influx()

        self.log(self.LOG_INFO, "Sending report to influx....")

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
