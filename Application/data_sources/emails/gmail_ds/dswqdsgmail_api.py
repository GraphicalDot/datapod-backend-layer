#-*- coding:utf-8 -*- 


import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .gmail_takeout import GmailsEMTakeout, PurchaseReservations
from .location import  LocationHistory
from sanic.exceptions import SanicException

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
GMAIL_BP = Blueprint("gmail", url_prefix="/gmail")








async def periodic(app, gmail_takeout_path):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')

    await asyncio.sleep(10)
    instance = GmailsEMTakeout(gmail_takeout_path, app.config.user_data_path, app.config.db_dir_path)
    instance.download_emails()



    logger.info('Periodic task has finished execution')
    return 

@GMAIL_BP.post('/takeout/parse')
async def parse(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path"], request.json)

    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")
    shutil.unpack_archive(request.json["path"], extract_dir=request.app.config.RAW_DATA_PATH, format=None)
    
        
    #request.app.add_task(periodic(request.app, path))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Takeout data parsing has been completed successfully"
        })


@GMAIL_BP.get('/takeout/purchase_n_reservations')
async def gmail_takeout(request):
    """
    To get all the assets created by the requester
    """
    
    path = os.path.join(request.app.config.user_data_path, "Takeout")
    
    if not os.path.exists(path):
        raise Exception(f"Path {path} doesnt exists")
    
    
    ins = PurchaseReservations(path, request.app.config.db_dir_path)
    ins.parse()

    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Successful"
        })






@GMAIL_BP.get('/takeout/location_history')
async def takeout_location_history(request):
    """
    To get all the assets created by the requester
    """
    
    path = os.path.join(request.app.config.user_data_path, "Takeout")
    
    if not os.path.exists(path):
        raise Exception(f"Path {path} doesnt exists")
    
    
    ins =  LocationHistory(path, request.app.config.db_dir_path)
    results = ins.format()
    
    return response.json(
        {
        'error': False,
        'success': True,
        "data": results
        })