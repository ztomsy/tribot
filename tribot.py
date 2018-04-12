from tkgtri import *
import ccxt
import sys
import json
import pprint


tribot = TriBot("_config_default.json")
tribot.test_balance = 1
tribot.debug = True
tribot.live = True

tribot.set_from_cli(sys.argv[1:]) # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename) # config taken from cli or default

print("OK")







