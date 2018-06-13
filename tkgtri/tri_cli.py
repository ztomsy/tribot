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

    parser.add_argument("--nolive", help="going into deals after max_past_triangles",
                        dest="live",
                        default=True,
                        action="store_false")

    parser.add_argument("--exchange", help="Seth the exchange_id. Ignore config file. ",
                        dest='exchange_id',
                        action="store", default=None)

    parser.add_argument("--balance", help="staring balance for fake deals. Default is 1",
                        dest="test_balance",
                        type=float,
                        action="store", default=None)

    parser.add_argument("--requests", help="maxumin requests to exchange per minute",
                        dest="max_requests_per_lap",
                        type=float,
                        action="store", default=None)


    return parser.parse_args(args)




