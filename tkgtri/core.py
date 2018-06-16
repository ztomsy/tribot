# for  basic exchange operations


def get_trade_direction_to_currency(symbol: str, dest_currency: str):
    cs = symbol.split("/")

    if cs[0] == dest_currency:
        return "buy"

    elif cs[1] == dest_currency:
        return "sell"

    else:
        return False


def get_symbol(c1: str, c2: str, markets: dict):
    if c1 + "/" + c2 in markets:
        a = c1 + "/" + c2
    elif c2 + "/" + c1 in markets:
        a = c2 + "/" + c1
    else:
        return False
    return a


def get_order_type(source_cur: str, dest_cur: str, symbol: str):

    if source_cur + "/" + dest_cur == symbol:
        a = "sell"
    elif dest_cur + "/" + source_cur == symbol:
        a = "buy"
    else:
        a = False

    return a


def get_symbol_order_price_from_tickers(source_cur: str, dest_cur: str, tickers: dict):
    if source_cur + "/" + dest_cur in tickers:
        symbol = source_cur + "/" + dest_cur
        order_type = "sell"
        price_type = "bid"

    elif dest_cur + "/" + source_cur in tickers:
        symbol = dest_cur + "/" + source_cur
        order_type = "buy"
        price_type = "ask"

    else:
        return None

    if symbol in tickers and price_type in tickers[symbol] and tickers[symbol][price_type] >0:
        price = tickers[symbol][price_type]
    else:
        price = None

    a = dict({"symbol": symbol, "order_type": order_type, "price_type": price_type, "price": price})
    return a











