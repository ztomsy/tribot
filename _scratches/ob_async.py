import multiprocessing as mp
# import tkgtri
from tkgtri import ccxtExchangeWrapper
import timeit
import ccxt.async as accxt
import asyncio


def ob_received(ob):
    pass
    # print("Ob received")
    # print(ob)


def pool_manager():
    pool = mp.Pool()

    for ob in order_books:
        pool.apply_async(exchange._ccxt.fetch_order_book, args=(ob,), callback=ob_received)

    pool.close()
    pool.join()


def consecutive():
    for ob in order_books:
        exchange._ccxt.fetch_order_book(ob)
        #print(ob)

class test_async(object):

    @staticmethod
    async def a_load_markets(exchange):
        await exchange.load_markets()


    async def get_ob_async(self, symbol, exchange_async):

        ob = await exchange_async.fetch_order_book(symbol)

        return ob


    def gel_all_oderbooks_async(self, symbols, exchange_async):
        loop = asyncio.get_event_loop()
        tasks = list()

        for s in symbols:
            tasks.append(self.get_ob_async(s, exchange_async))

        ob_array = loop.run_until_complete(asyncio.gather(*tasks))

        return ob_array


def async():
    ta = test_async()
    obs = ta.gel_all_oderbooks_async(order_books, exchange_async)
    print(len(obs))


def async_exchangeWrapper():
    exchange.get_oder_books_async(order_books)


order_books = ["ETH/BTC", "ETH/USDT", "BTC/USDT"]

exchange = ccxtExchangeWrapper.load_from_id("binance")
exchange.get_markets()

exchange_async = accxt.binance()
loop = asyncio.get_event_loop()
loop.run_until_complete(test_async.a_load_markets(exchange_async))

exchange.init_async_exchange()


# pool_manager()
# consecutive()
async_exchangeWrapper()
#async()
num_of_runs = 5

t = dict()

t["async_time"] = timeit.timeit("async()", setup="from __main__ import async", number=num_of_runs)
t["pool_manager"] = timeit.timeit("pool_manager()", setup="from __main__ import pool_manager", number=num_of_runs)
t["consecutive"] = timeit.timeit("consecutive()", setup="from __main__ import consecutive", number=num_of_runs)
t["async_exchangeWrapper"] = timeit.timeit("async_exchangeWrapper()",
                                           setup="from __main__ import async_exchangeWrapper",
                                           number=num_of_runs)

for i in t:
    print("{}:{}".format(i, t[i] / num_of_runs))










