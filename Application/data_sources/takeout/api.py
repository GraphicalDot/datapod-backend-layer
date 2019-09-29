import shutil
import asyncio
from sanic import Blueprint
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .parse_emails import EmailParse
from .location import  LocationHistory
from .purchases_n_reservations import PurchaseReservations
import base64
import  database_calls.db_purchases as q_purchase_db
import  database_calls.db_reservations as q_reservation_db
import  database_calls.db_images as q_images_db
from   database_calls.takeout.db_emails  import match_text as e_match_text
from database_calls.takeout.db_emails  import  get_email_attachment, get_emails, search_emails
from utils.utils import check_production
from .images import ParseGoogleImages
import datetime
import asyncio
import functools
from functools import partial
import concurrent.futures
from websockets.exceptions import ConnectionClosed
from utils.utils import async_wrap, send_sse_message
import base64
from io import BytesIO
from PIL import Image
import dateparser
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

    for args in images_data:
        await q_images_db.store(**args)

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


    # await asyncio.wait(
    #         fs=[loop.run_in_executor(executor,  
    #             functools.partial(q_purchase_db.store, **purchase)) for purchase in purchases],
    #         return_when=asyncio.ALL_COMPLETED)
    for purchase in purchases:
        await q_purchase_db.store(**purchase)
    
    # await asyncio.wait(
    #         fs=[loop.run_in_executor(executor,  
    #             functools.partial(q_reservation_db.store, **reservation)) for reservation in reservations],
    #         return_when=asyncio.ALL_COMPLETED)
    
    for reservation in reservations:
        await q_reservation_db.store(**reservation)
    



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
    email_parsing_instance = await EmailParse(config)

    ##parsing all the email data from the takeout
    await email_parsing_instance.download_emails()
    #await config.SIO.emit("takeout_response", {'data': i }, namespace="/takeout")
    #await broadcast(config, i)
    try:
        ins = await ParseGoogleImages(config)
        await ins.parse()
        images_data = ins.images_data

        for image_data in images_data:
            logger.info(image_data)
            image_data.update({"tbl_object": config.IMAGES_TBL}) 
            await q_images_db.store(**image_data)
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
        await q_purchase_db.store(**purchase)

    for reservation in reservations:
        reservation.pop("products")
        reservation.update({"tbl_object": config.RESERVATIONS_TBL}) 
        await q_reservation_db.store(**reservation)
        
    logger.info('Periodic task has finished execution')

    await email_parsing_instance.send_sse_message(100)

    # ##updating datasources table with the status that parsing of the takeout is completed
    logger.info("Trying to update data source table with status completed")
    email_parsing_instance.update_datasource_table("COMPLETED", email_parsing_instance.email_count)
    # logger.info("Updated data source table with status completed")
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


    mbox_file = os.path.join(request.app.config.RAW_DATA_PATH,  "Takeout/Mail")
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

@async_wrap
def image_base64(path):
    try:
        image = Image.open(path)
        buffered = BytesIO()
        image.save(buffered, format=image.format)
        img_str = base64.b64encode(buffered.getvalue())
    except Exception as e:
        logger.error(f"Error {e} while converting fb image to base64")
    return img_str.decode()




# @TAKEOUT_BP.get('images/filter')
# async def images_filter(request):
#     """
#     To get all the assets created by the requester
#     """
#     #request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)
#     if request.args.get("page"):
#         page = request.args.get("page")
#     else:
#         page = 1


#     if request.args.get("number"):
#         number = request.args.get("number")
#     else:
#         number = 20


#     images = q_images_db.filter_images(request.app.config.IMAGES_TBL, page, number,  time=None)
#     for image in images:
#         b64_data = await image_base64(image['image_path'])
#         creation_time = image.pop("creation_time")
#         encoded_string = "data:image/jpeg;base64," + b64_data
#         #data:image/png;base64
#         image.update({"creation_time": creation_time.strftime("%Y-%m-%d"), "uri": encoded_string})

#     logger.success(images)
#     return response.json(
#         {
#         'error': False,
#         'success': True,
#         "data": images,
#         "message": None
#         })


@TAKEOUT_BP.get('images/filter')
async def images_filter(request):

    logger.info("Number is ", request.args.get("limit"))
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 

    logger.info(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    logger.info(f"This is the start_date {start_date}")
    logger.info(f"This is the end_date {end_date}")



    images, count = await q_images_db.filter_images(request.app.config.IMAGES_TBL, start_date, end_date, int(skip), int(limit))
    logger.info(images)
    for image in images:
        b64_data = await image_base64(image['image_path'])
        creation_time = image.pop("creation_time")
        encoded_string = "data:image/jpeg;base64," + b64_data
        #data:image/png;base64
        image.update({"creation_time": creation_time.strftime("%Y-%m-%d"), "uri": encoded_string})

    # [repo.update({
    #         "created_at":repo.get("created_at").strftime("%d, %b %Y"),
    #     }) for repo in result]

    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"images": images, "count": count},
        'message': None
        })



@TAKEOUT_BP.get('attachements/filter')
async def attachements_filter(request):
    """
    To get all the assets created by the requester
    """
    logger.info(f"Args are {request.args.items()}")
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 50][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 

    logger.info(f"Skip type is {skip}")
    logger.info(f"limit type is {limit}")
    logger.info(f"start date type is {start_date}, and type is {type(start_date)}")

    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    logger.info(f"This is the start_date {start_date}")
    logger.info(f"This is the end_date {end_date}")

    attachments = await get_email_attachment(request.app.config.EMAIL_ATTACHMENT_TBL, start_date, end_date, int(skip), int(limit))
    # for iage in images:
    #     creation_time = image.pop("creation_time")
    #     #data:image/png;base64
    #     image.update({"creation_time": creation_time.strftime("%Y-%m-%d")})

    logger.success(attachments)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": attachments,
        "message": None
        })




@TAKEOUT_BP.get('emails/filter')
async def emails_filter(request):
    """
    To get all the assets created by the requester
    """

    logger.info(f"Args are {request.args.items()}")
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 50][request.args.get("limit") == None] 
    matching_string = request.args.get("match_string") 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    message_type = request.args.get("message_type")

    logger.info(f"Message type is {message_type}")
    logger.info(f"Skip type is {skip}")
    logger.info(f"limit type is {limit}")
    logger.info(f"start date type is {start_date}, and type is {type(start_date)}")

    logger.info(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    logger.info(f"This is the start_date {start_date}")
    logger.info(f"This is the end_date {end_date}")


    if matching_string:
        emails = await search_emails(request.app.config.EMAILS_TBL, message_type, start_date, end_date, int(skip), int(limit), matching_string)
    else:
        logger.info("Without matching string")
        emails, count = await get_emails(request.app.config.EMAILS_TBL, message_type, start_date, end_date, int(skip), int(limit))


    # emails = await get_emails(request.app.config.EMAILS_TBL, page, number, message_type)
    for email in emails:
        creation_time = email.pop("date")
        #data:image/png;base64
        email.update({"date": creation_time.strftime("%d %b, %Y")})

    logger.success(f"Number of emails are {count}")
    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"emails": emails, "count": count},
        "message": None
        })



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


    logger.info(request.args)
    logger.info(f"This is the matching string {matching_string}")


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
