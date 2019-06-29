import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
import tarfile
import gzip
from binance.client import Client
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
from database_calls.crypto.db_binance import store, get_creds
from .binance_ds.binance import binance_client, get_all_tickers, get_all_orders

verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
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