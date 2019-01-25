

====================================

TTTTTTTTTT    K    K     GGGGG
    T         K   K     G
    T         KKKK      G
    T         K  K      G    GG
    T         K   K     G      G
    t         K    K     GGGGGGG

=====================================


TKG-Production for TRIANGULAR Arbitrage

---------------
Installation:

cd tkg-production
pip3 install -r requirements.txt
pip3 install -e .

Run the tests: python3 -m unittest -v -b

---------------

Usage:

1. Offline test:
    python3 tribot.py --config=_kucoin.json --offline --force --force_start_bid 0.1 --runonce --balance 1

2. launch with default config (_config_default.json): python3 tribot.py

cli parameters: python3 tribot.py --help

default config: _config_default.json

---------------


Project structure have been taken from  `<http://www.kennethreitz.org/essays/repository-structure-and-python>`_.
If you want to learn more about ``setup.py`` files, check out `this repository <https://github.com/kennethreitz/setup.py>`_.
