


from database_calls.crypto.db_binance import get_creds



async def binance_client():
    data = get_creds()


async def get_all_tickers():

    pass


async def get_all_orders():
    pass


async def get_order_pair():
    """
    Get orders for a single pair like
    """


def for ticker in tickers[0:10]: 
    ...:     orders = client.get_all_orders(symbol=ticker["symbol"], limit=10) 
    ...:     print (orders) 