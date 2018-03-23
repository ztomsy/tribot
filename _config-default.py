
# filter on starting currency in triangles
start_cur = "ETH"

# share of balance to bid
bal_share_to_bid = 0.8  #

# maximum recovery attemts in case if trade 2 or 3 failed
max_recovery_attempts = 20

# trade volume limits for appropriate quote currency ( market currency)
lot_limits = {"BTC": 0.002, "ETH": 0.02, "BNB": 1, "USDT": 20}

# used in result calculation
commission = 0.0005

# result of trianle
threshold = 1.005
threshold_orderbook = 1.005

api_key = {"apiKey": "testApiKey",
           "secret": "testApiSecret"}

# how much tickers to save on deal
max_past_triangles = 100

# how much tickers to save on deal
good_consecutive_results_threshold = 2

# time in seconds to consider maximum transactions per lap
lap_time = 60
max_transactions_per_lap = 850