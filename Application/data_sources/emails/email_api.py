import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .gmail_ds.gmail_takeout import GmailsEMTakeout, PurchaseReservations
from .gmail_ds.location import  LocationHistory
from .gmail_ds.purchases_n_reservations import PurchaseReservations
from sanic.exceptions import SanicException
from pprint import pprint
import  database_calls.db_purchases_n_reservations as q_purchase_db
import  database_calls.db_images as q_images_db

from .gmail_ds.images import ParseGoogleImages

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
EMAIL_BP = Blueprint("", url_prefix="/")




async def periodic(app, gmail_takeout_path):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')

    await asyncio.sleep(10)
    instance = GmailsEMTakeout(gmail_takeout_path, app.config.user_data_path, app.config.db_dir_path)
    instance.download_emails()



    logger.info('Periodic task has finished execution')
    return 

@EMAIL_BP.post('gmail/takeout/parse')
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


@EMAIL_BP.get('gmail/takeout/purchase_n_reservations')
async def gmail_takeout(request):
    """
    To get all the assets created by the requester
    """
    
    path = os.path.join(request.app.config.RAW_DATA_PATH, "Takeout")
    
    if not os.path.exists(path):
        raise Exception(f"Path {path} doesnt exists")
    
    
    ins = await PurchaseReservations(path, request.app.config)
    reservations, purchases = await ins.parse()
    
    for purchase in purchases:
        #print (purchase)
        q_purchase_db.store_purchase(request.app.config.PURCHASES_TBL, purchase)


    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Successful"
        })



@EMAIL_BP.post('gmail/takeout/purchase_n_reservations/filter')
async def purchase_n_reservation_filter(request):
    """
    Page is the page number 
    NUmber is the number of items on the page 
    """
    request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)


    result =  [q_purchase_db.format(request.app.config, purchase) for purchase in \
                q_purchase_db.filter_merchant_name(request.app.config.PURCHASES_TBL, 
                request.json["page"], request.json["number"],  request.json.get("merchant_name"))] 

    return response.json(
        {
        'error': False,
        'success': True,
        "data": result,
        "message": None
        })



@EMAIL_BP.get('takeout/images')
async def images(request):
    """
    To get all the assets created by the requester
    """
    
    path = os.path.join(request.app.config.RAW_DATA_PATH, "Takeout")
    
    if not os.path.exists(path):
        raise Exception(f"Path {path} doesnt exists")
    
    
    ins = await ParseGoogleImages(path, request.app.config)
    await ins.parse()
    images_data = ins.images_data

    for image_data in images_data:
        image_data.update({"tbl_object": request.app.config.IMAGES_TBL}) 
    
    await asyncio.gather(*[q_images_db.store(**image_data) for image_data in images_data])
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Successful"
        })

@EMAIL_BP.get('gmail/takeout/location_history')
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