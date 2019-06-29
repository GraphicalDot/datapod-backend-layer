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
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
CRYPTO_BP = Blueprint("crypto", url_prefix="")
from database_calls.crypto.db_binance import store


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


