import argparse


def get_cli_parameters(args):
    parser = argparse.ArgumentParser()

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
                        help="ignore max amount for order books and use this amount to start deals",
                        dest="force_start_amount",
                        default=None,
                        type=float,
                        action="store")

    parser.add_argument("--noauth",
                        help="do not use the credentianls for exchange",
                        dest="noauth",
                        default=False,
                        action="store_true")

    subparsers = parser.add_subparsers(help="Running mode. Online in default")
    subparsers.required = False
    offline = subparsers.add_parser("offline", help="Set the working  mode")
    # offline = subparsers.add_parser("online", help="Set the offline mode")
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

    return parser.parse_args(args)
