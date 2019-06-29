


from database_calls.crypto.db_binance import get_creds, store_pairs
from binance.client import Client 
import asyncio
import time
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def binance_client(api_key, api_secret):
    """
    No need to check the secrets as they were checked when they first was inserted into the 
    database

    """
    client = Client(api_key, api_secret)                                                                                                                                                                                                                                             
    return client


def get_all_tickers(client):
    tickers = client.get_orderbook_tickers() 
    return tickers


async def get_all_orders(app_config, client, pair_list):
    """ 
    cient is binance api client 
    pair_list is list of trading pairs
    i.e  'STRATBTC','STRATETH', 'SNGLSBTC', 'SNGLSETH', 'BQXBTC',
        'BQXETH','KNCBTC'
    """

    #result = await asyncio.gather(*[_get_order_pair(client, pair) for pair in pair_list])
    result = {}
    for pair in pair_list:
        orders = await _get_order_pair(client, pair)
        logger.info(orders)
        store_pairs(app_config.DB_OBJECT, app_config.CRYPTO_EXG_BINANCE, orders)


        result.update({pair: orders})
        time.sleep(0.5)
    return result

async def _get_order_pair(client, pair):
    """
    Get orders for a single pair like
    #TODO handle limit 10
    """
    try:
        orders = client.get_all_orders(symbol=pair, limit=1000)
        logger.success(f"Success in fetching pair {pair} with orders length {len(orders)}")
    except Exception as e:
        logger.error(f"Error in fetching {pair} with error {e}")
        return (pair, "")
    return orders
