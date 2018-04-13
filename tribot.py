from tkgtri import *
import ccxt
import sys
import json
import pprint
import logging

tribot = TriBot("_config_default.json", "_tri.log")
tribot.print_logo("TriBot v 0.5")
tribot.set_log_level(tribot.LOG_INFO)

tribot.log(tribot.LOG_CRITICAL, "Started")


tribot.test_balance = 1
tribot.debug = True
tribot.live = True

tribot.set_from_cli(sys.argv[1:])  # cli parameters  override config
tribot.load_config_from_file(tribot.config_filename)  # config taken from cli or default

tribot.log(tribot.LOG_CRITICAL, "Finished")







