import ccxt
import json
import collections
import time
import csv
import tkgtri
import tkgtri.utils as utils

tkgtri.tribot.TriBot.print_logo("tools")
print("Fetch markets+tickers data and dump it to files.")
print("For settings edit source file.")
print("-----------------------------------")

exchange_id = "binance"
markets_file = "test_data/markets_binance.json"
tickers_file = "test_data/tickers_binance.csv"

markets_file = utils.get_next_filename_index(markets_file)
tickers_file = utils.get_next_filename_index(tickers_file)

print("Markets file:" + markets_file)
print("Tickers file:" + tickers_file)

# create markets and tickers files for offline testing

# ETH-XEM-BTC: buy sell buy ;  XEM/ETH, XEM/BTC, ETH/BTC
# ETH-USDT-BTC: sell-buy-buy ; ETH/USDT BTC/USDT ETH/BTC
# ETH-BTC-TRX: sell-buy-sell ; ETH/BTC TRX/BTC TRX/ETH
# ETH-AMB-BNB: buy-sell-sell ; AMB/ETH AMB/BNB BNB/ETH

number_tickers_to_save = 3
tickers_fields = ["timestamp","symbol","ask", "bid", "askVolume", "bidVolume"]

tickers_csv_header = ["fetch_id"]+tickers_fields

triangles = [["XEM/ETH", "XEM/BTC", "ETH/BTC"], ["ETH/USDT", "BTC/USDT", "ETH/BTC"], ["ETH/BTC", "TRX/BTC", "TRX/ETH"],
            ["AMB/ETH", "AMB/BNB", "BNB/ETH"]]

symbols =  [s for t in triangles for s in t]


e = eval("ccxt.{}()".format(exchange_id))

print("Loading markets")
markets = e.load_markets()
markets_to_save = collections.OrderedDict()
markets_to_save = {s: markets[s] for s in symbols}
print("Saving markets")
with open(markets_file, 'w') as outfile:
    json.dump(markets, outfile)


tickers = collections.OrderedDict()
tickers_to_save = list()

for i in range(0, number_tickers_to_save):
    print("Fetching tickers...{} of {}".format(i+1, number_tickers_to_save))
    tickers = e.fetch_tickers(symbols)

    # save only needed fields and add fetch_id
    for t in tickers:
        t_dict = { your_key: tickers[t][your_key] for your_key in tickers_fields }
        t_dict["fetch_id"] = i
        tickers_to_save.append (t_dict)
    print(".. pause")
    time.sleep(1)

print("Saving tickers....")

with open(tickers_file, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, tickers_csv_header)
    dict_writer.writeheader()
    dict_writer.writerows(tickers_to_save)

print("Done!")