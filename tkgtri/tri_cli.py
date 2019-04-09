import argparse

class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


def get_cli_parameters(args):
    parser = argparse.ArgumentParser(formatter_class=SmartFormatter)

    parser.add_argument("--config", help="config file",
                        dest="config_filename",
                        action="store", default=None)

    parser.add_argument("--debug", help="If debug enabled - exit when error occurs. ",
                        dest="debug",
                        default=False,
                        action="store_true")

    parser.add_argument("--force", help="going into deals after max_past_triangles with the best tri",
                        dest="force_best_tri",
                        default=False,
                        action="store_true")

    parser.add_argument("--exchange", help="Seth the exchange_id. Ignore config file. ",
                        dest='exchange_id',
                        action="store", default=None)

    parser.add_argument("--balance", help="Staring balance. if no value set - 1 by default",
                        dest="test_balance",
                        type=float,
                        action="store", const=1, nargs="?")

    parser.add_argument("--requests", help="maximum requests to exchange per minute",
                        dest="max_requests_per_lap",
                        type=float,
                        action="store", default=None)

    parser.add_argument("--runonce", help="run only one set of deals and finish",
                        dest="run_once",
                        default=False,
                        action="store_true")

    parser.add_argument("--force_start_bid",
                        help="Set the starting bid amount. Ignore the max bid checking because of results thresholds. "
                             "Mainly used for tests with the --force when it's needed to run test through whole"
                             " triangle with amount bigger than min amount ",
                        dest="force_start_amount",
                        default=None,
                        type=float,
                        action="store")

    parser.add_argument("--override_depth_amount",
                        help="Override the start amount from the order books when it is less than this parameter. "
                             "In this case ticker prices will be used.",
                        dest="override_depth_amount",
                        default=None,
                        type=float,
                        action="store")

    parser.add_argument("--skip_order_books",
                        help="R|Do not check order books!!\n"
                             "In this case the start amount will be set from (in order of priority):\n"
                             "1. override_depth_amount (if present) \n"
                             "2. force_start_bid (if present)\n"
                             "3. max bid from the threshold configuration (balance_bid_thresholds) \n",
                        dest="skip_order_books",
                        default=False,
                        action="store_true")

    parser.add_argument("--noauth",
                        help="do not use the credentianls for exchange",
                        dest="noauth",
                        default=False,
                        action="store_true")

    parser.add_argument("--verbose",
                        help="Set log level DEBUG",
                        dest="verbose",
                        default=False,
                        action="store_true")

    subparsers = parser.add_subparsers(help="Offline mode")
    subparsers.required = False
    offline = subparsers.add_parser("offline", help="Set the working  mode. offline -h for help")
    # online = subparsers.add_parser("online", help="Set the online mode")
    offline.set_defaults(offline=True)

    offline.add_argument("--tickers", "-t",
                         help="path to csv tickers file",
                         dest="offline_tickers_file",
                         default=None,
                         action="store")

    offline.add_argument("--order_books","-ob",
                         help="path to csv order books file",
                         dest="offline_order_books_file",
                         default=None,
                         action="store")

    offline.add_argument("--markets", "-m",
                         help="path to markets json file",
                         dest="offline_markets_file",
                         default=None,
                         action="store")

    offline.add_argument("--test",
                         help="Test run. Deal uuid is forced to be a 'test'. Reports saved into _test folder. "
                              "Previous test files renamed into test_X.csv",
                         dest="offline_run_test",
                         default=None,
                         action="store_true")

    offline.add_argument("--deal", "-d",
                         help="load offline tickers, markets and order books from <deal_uuid>.csv, "
                              "<deal_uuid>_markets.csv "
                              "<deal_uuid>_ob.csv",
                         dest="offline_deal_uuid",
                         default=None,
                         action="store")



    return parser.parse_args(args)
