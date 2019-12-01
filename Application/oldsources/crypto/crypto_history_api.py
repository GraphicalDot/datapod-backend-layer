import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
import tarfile
import gzip
import datetime
from binance.client import Client
from errors_module.errors import APIBadRequest
from database_calls.crypto.db_binance import store, get_creds, get_pairs, filter_pair
from .binance_ds.binance import binance_client, get_all_tickers, get_all_orders

from loguru import logger
CRYPTO_BP = Blueprint("crypto", url_prefix="")



@CRYPTO_BP.post('/creds/binance')
async def creds_binance(request):
    """
    """

    request.app.config.VALIDATE_FIELDS(["api_secret", "api_key"], request.json)
    try:
        client = Client(request.json["api_key"], request.json["api_secret"]) 
        res = client.get_account_status() 
        if not res["success"]:
            raise APIBadRequest("Your account has some problems") 
    except Exception:
        raise APIBadRequest("The api key or api secret for binanace are wrong")

    store(request.app.config.CRYPTO_CRED_TBL, request.json["api_key"], request.json["api_secret"])

    return response.json(
        {
        'error': False,
        'success': True,
        })


@CRYPTO_BP.get('/store/binance')
async def store_binance(request):
    api_key, api_secret = get_creds(request.app.config.CRYPTO_CRED_TBL)
    client = binance_client(api_key, api_secret)
    tickers = [e["symbol"] for e in get_all_tickers(client)]
    logging.info(f"Api key {api_key}")
    logging.info(f"Api secret {api_secret}")
    res = await get_all_orders(request.app.config, client, tickers)


    return response.json(
        {
        'error': False,
        'success': True,
        'data': res,
        'messege': None
        })



@CRYPTO_BP.get('/binance/all_pairs')
async def all_pairs_binance(request):

    res = get_pairs(request.app.config.CRYPTO_EXG_BINANCE)

    return response.json(
        {
        'error': False,
        'success': True,
        'data': res,
        'messege': None
        })

@CRYPTO_BP.get('/binance/filter_pair')
async def all_pairs_binance(request):
    args = RequestParameters()
    
    if args.get("page"):
        page = args.get("page")
    else:
        page=1

    if args.get("number"):
        number= args.get("number")
    else:
        number=100
    
    if args.get("pair_name"):
        number= args.get("pair_name")
    else:
        pair_name=None

    """    
        'id': 119,
        'symbol': 'WABIBTC',
        'order_id': 2379648,
        'client_order_id': 'hb8f37EjiIawsDRh8CJMTO',
        'price': '0.00038276',
        'orig_qty': '42.00000000',
        'executed_qty': '42.00000000',
        'cummulative_quote_qty': '0.01607592',
        'status': 'FILLED',
        'time_in_force': 'GTC',
        '_type': 'LIMIT',
        'side': 'BUY',
        'stop_price': '0.00000000',
        'iceberg_qty': '0.00000000',
        'time': 1515615532962,
        'update_time': 1515615545528,
        'is_working': True},
    """

    res = [{"symbol": pair["symbol"], "price": pair["price"], 
            "orig_qty": pair["orig_qty"], "executed_qty": pair["executed_qty"],
             "status": pair["status"], "side": pair["side"],
             "time": datetime.datetime.fromtimestamp(pair["time"]/1000.0).strftime("%d %b,%y")
             }  for pair in filter_pair(request.app.config.CRYPTO_EXG_BINANCE, pair_name, page, number)]
    


    
    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"result" : res, "headers":   list(res[0].keys()) },
        'messege': None
        })