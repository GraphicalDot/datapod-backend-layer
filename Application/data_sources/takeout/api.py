import shutil
import asyncio
from sanic import Blueprint
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .parse_emails import TakeoutEmails
from .location import  LocationHistory
from .purchases_n_reservations import PurchaseReservations
import base64
import  database_calls.db_purchases as q_purchase_db
import  database_calls.db_reservations as q_reservation_db
import  database_calls.db_images as q_images_db
from   database_calls.db_emails  import match_text as e_match_text
from utils.utils import check_production
from .images import ParseGoogleImages
import datetime
import asyncio
import functools
import coloredlogs, verboselogs, logging
from functools import partial
import concurrent.futures
from websockets.exceptions import ConnectionClosed


import string
import random
import time
from loguru import logger

TAKEOUT_BP = Blueprint("", url_prefix="/takeout/")



async def parse_images(config, loop, executor):
    path = os.path.join(config.RAW_DATA_PATH, "Takeout")

    ins = await ParseGoogleImages(path, config)
    await ins.parse()
    images_data = ins.images_data

    for image_data in images_data:
        image_data.update({"tbl_object": config.IMAGES_TBL}) 
        

    _, _ = await asyncio.wait(
            fs=[loop.run_in_executor(executor, 
                    functools.partial(q_images_db.store, **args)) for args in images_data],
            return_when=asyncio.ALL_COMPLETED
        )

    return 

async def purchase_n_reservations(config, loop, executor):
    path = os.path.join(config.RAW_DATA_PATH, "Takeout")

    try:
        ins = await PurchaseReservations(path, config)
    except Exception as e:
        logger.error(f"Parsing of purchases and reservations failed {e}")
    reservations, purchases = await ins.parse()
    

    for purchase in purchases:
        purchase.update({"tbl_object": config.PURCHASES_TBL}) 

    for reservation in reservations:
        reservation.pop("products")
        reservation.update({"tbl_object": config.RESERVATIONS_TBL}) 


    await asyncio.wait(
            fs=[loop.run_in_executor(executor,  
                functools.partial(q_purchase_db.store, **purchase)) for purchase in purchases],
            return_when=asyncio.ALL_COMPLETED)
    
    await asyncio.wait(
            fs=[loop.run_in_executor(executor,  
                functools.partial(q_reservation_db.store, **reservation)) for reservation in reservations],
            return_when=asyncio.ALL_COMPLETED)
    



    return 


async def asyncparse_takeout(config, loop, executor):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')

    instance = TakeoutEmails(config)

    await asyncio.gather(*[
                instance.download_emails(loop, executor), 
                parse_images(config, loop, executor),
                purchase_n_reservations(config, loop, executor)
                ])

    logger.info('Periodic task has finished execution')

    
    return 


# async def broadcast(config, message):
#     broadcast = config.SIO.emit("takeout_response", {'data': message }, namespace="/takeout")

#     #broadcasts = [ws.send(message) for ws in app.ws_clients]
#     #for result in asyncio.as_completed(broadcasts):
#     try:
#         await asyncio.wait(broadcast)
#         logger.info(f"completed {message}")
    
#     except Exception as ex:
#         template = f"An exception of type {ex} occurred"
#         logger.error(template)
#     return 




async def parse_takeout(config):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')
    #path = os.path.join(config.RAW_DATA_PATH, "Takeout")

    email_parsing_instance = TakeoutEmails(config)

    ##parsing all the email data from the takeout
    await email_parsing_instance.download_emails()
    #await config.SIO.emit("takeout_response", {'data': i }, namespace="/takeout")
    #await broadcast(config, i)

    try:
        ins = await ParseGoogleImages(config)
        await ins.parse()
        images_data = ins.images_data

        for image_data in images_data:
            image_data.update({"tbl_object": config.IMAGES_TBL}) 
            q_images_db.store(**image_data)
    except Exception as e:
        logger.error(f"Parsing Image data Failed {e}")    
        pass
    await email_parsing_instance.send_sse_message(99)


    try:
        ins = await PurchaseReservations(config)
        reservations, purchases = await ins.parse()
    except Exception as e:
        logger.error(f"Purchases and reservation parsing failed {e}")    
        return                                                                        

    for purchase in purchases:
        purchase.update({"tbl_object": config.PURCHASES_TBL}) 
        q_purchase_db.store(**purchase)

    for reservation in reservations:
        reservation.pop("products")
        reservation.update({"tbl_object": config.RESERVATIONS_TBL}) 
        q_reservation_db.store(**reservation)
        
    logger.info('Periodic task has finished execution')

    await email_parsing_instance.send_sse_message(100)

    ##updating datasources table with the status that parsing of the takeout is completed
    email_parsing_instance.update_datasource_table("COMPLETED", email_parsing_instance.email_count)

    return 






#@TAKEOUT_BP.websocket('parse')
@TAKEOUT_BP.post('parse')
async def parse_takeout_api(request):
    """
    To get all the assets created by the requester
    """
    import zipfile
    request.app.config.VALIDATE_FIELDS(["path"], request.json)




    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    try:
        the_zip_file = zipfile.ZipFile(request.json["path"])
    except:
        raise APIBadRequest("Invalid zip takeout file")


    logger.info(f"Testing zip {request.json['path']} file")
    ret = the_zip_file.testzip()

    if ret is not None:
        raise APIBadRequest("Invalid zip takeout file")

    ##check if mbox file exists or not



    logger.info("Copying and extracting takeout data")

    try:
        shutil.unpack_archive(request.json["path"], extract_dir=request.app.config.RAW_DATA_PATH, format=None)
    except:
        raise APIBadRequest("Invalid zip takeout file")


    mbox_file = os.path.join(request.app.config.RAW_DATA_PATH,  "Takeout/Mail/All mail Including Spam and Trash.mbox")
    if not os.path.exists(mbox_file):
        raise APIBadRequest(f"This is not a valid takeout zip {mbox_file}")



    request.app.add_task(parse_takeout(request.app.config))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Takeout data parsing has been Started and you will be notified once it is complete", 
        "data": None
        })


@TAKEOUT_BP.get('purchase_n_reservations')
@check_production()
async def purchase_n_reservations_api(request):
    """
    To get all the assets created by the requester
    """
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    await purchase_n_reservations(request.app.config, loop, executor)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Successful"
        })






@TAKEOUT_BP.get('purchases/filter')
async def purchase_filter(request):
    """
    Page is the page number 
    NUmber is the number of items on the page 
    """
    #request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)

    if request.args.get("page"):
        try:
            page = int(request.args.get("page"))
        except:
            raise APIBadRequest("Invalid page type")

    else:
        page = 1


    if request.args.get("number"):
        try:
            number = int(request.args.get("number"))
        except:
            raise APIBadRequest("Invalid Number type")
    else:
        number = request.app.config.DEFAULT_ITEMS_NUMBER


    result =  [q_purchase_db.format(request.app.config, purchase) for purchase in \
                q_purchase_db.filter_merchant_name(request.app.config.PURCHASES_TBL, 
                page, number,  request.args.get("merchant_name"))] 

    return response.json(
        {
        'error': False,
        'success': True,
        "data": result,
        "message": None
        })


@TAKEOUT_BP.get('reservations/filter')
async def reservations_filter(request):
    """
    Page is the page number 
    NUmber is the number of items on the page 
    """
    #request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)

    if request.args.get("page"):
        try:
            page = int(request.args.get("page"))
        except:
            raise APIBadRequest("Invalid page type")

    else:
        page = 1


    if request.args.get("number"):
        try:
            number = int(request.args.get("number"))
        except:
            raise APIBadRequest("Invalid Number type")
    else:
        number = request.app.config.DEFAULT_ITEMS_NUMBER


    result =  [purchase for purchase in \
                q_reservation_db.filter_merchant_name(request.app.config.RESERVATIONS_TBL, 
                page, number,  request.args.get("merchant_name"))] 

    return response.json(
        {
        'error': False,
        'success': True,
        "data": result,
        "message": None
        })






@TAKEOUT_BP.get('images/filter')
async def images_filter(request):
    """
    To get all the assets created by the requester
    """
    #request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)
    if request.args.get("page"):
        page = request.args.get("page")
    else:
        page = 1


    if request.args.get("number"):
        number = request.args.get("number")
    else:
        number = 200


    images = q_images_db.filter_date(request.app.config.IMAGES_TBL, page, number,  time=None)
    for image in images:
        creation_time = image.pop("creation_time")
        #data:image/png;base64
        image.update({"creation_time": creation_time.strftime("%Y-%m-%d")})

    logger.success(images)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": images,
        "message": None
        })





# @TAKEOUT_BP.get('images')
# @check_production()
# async def parse_images_api(request):
#     """
#     To get all the assets created by the requester
#     """
#     loop = asyncio.get_event_loop()
#     executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    
#     await prase_images(request.app.config)
#     return response.json(
#         {
#         'error': False,
#         'success': True,
#         "data": "Successful"
#         })





@TAKEOUT_BP.get('location_history')
@check_production()
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
    

@TAKEOUT_BP.get('email/match_text')
async def match_text_email(request):
    


    if request.args.get("page"):
        page = request.args.get("page")
    else:
        page = 1


    if request.args.get("number"):
        number = request.args.get("number")
    else:
        number = 200

    if not request.args.get("match_string"):
        raise APIBadRequest("get params match_string is required")

    matching_string = request.args.get("match_string") 


    logging.info(request.args)
    logging.info(f"This is the matching string {matching_string}")


    res = e_match_text(request.app.config.EMAILS_TBL, request.app.config.INDEX_EMAIL_CONTENT_TBL, \
            matching_string , page, number)

    return response.json(
        {
        'error': False,
        'success': True,
        "data": res
        })

    # while True:
    #     data = 'hello!'
    #     print('Sending: ' + data)
    #     await ws.send(data)
    #     data = await ws.recv()
    #     print('Received: ' + data)
