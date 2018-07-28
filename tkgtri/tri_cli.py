import argparse


def get_cli_parameters(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", help="config file",
                        dest="config_filename",
                        action="store", default=None)

    parser.add_argument("--nodebug", help="actual deals",
                        dest="debug",
                        default=True,
                        action="store_false")

    parser.add_argument("--force", help="going into deals after max_past_triangles with the best tri",
                        dest="force_best_tri",
                        default=False,
                        action="store_true")

    parser.add_argument("--exchange", help="Seth the exchange_id. Ignore config file. ",
                        dest='exchange_id',
                        action="store", default=None)

    parser.add_argument("--balance", help="staring balance for fake deals",
                        dest="test_balance",
                        type=float,
                        action="store", default=None)

    parser.add_argument("--requests", help="maximum requests to exchange per minute",
                        dest="max_requests_per_lap",
                        type=float,
                        action="store", default=None)

    parser.add_argument("--runonce", help="run only one set of deals and finish",
                        dest="run_once",
                        default=False,
                        action="store_true")

    parser.add_argument("--force_start_bid", help="ignore max amount for order books and use this amount to start deals",
                        dest="force_start_amount",
                        default=None,
                        type=float,
                        action="store")

    parser.add_argument("--noauth",
                        help="do not use the credentianls for exchange",
                        dest="noauth",
                        default=False,
                        action="store_true")


    return parser.parse_args(args)




