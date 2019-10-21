import shutil
import asyncio
from sanic import Blueprint
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .utils.parse_emails import EmailParse
from  .utils.location import  LocationHistory
from .utils.purchases_n_reservations import PurchaseReservations
import base64

# import  database_calls.db_purchases as q_purchase_db
# import  database_calls.db_reservations as q_reservation_db
# import  database_calls.db_images as q_images_db
# from   database_calls.takeout.db_emails  import match_text as e_match_text
# from database_calls.takeout.db_emails  import  get_email_attachment, get_emails, match_text



from .utils.images import ParseGoogleImages
import datetime
import json
import asyncio
import functools
from functools import partial
import concurrent.futures
import base64
from io import BytesIO
from PIL import Image
import dateparser
import string
import random
import time
from loguru import logger
from datasources.shared.extract import extract
import aiomisc

from .db_calls import update_datasources_status, get_emails, match_text, filter_images, filter_attachments, filter_purchases, filter_reservations
from .variables import DATASOURCE_NAME







async def stats(request):
    res = await get_stats(request.app.config[DATASOURCE_NAME]["tables"]["stats_table"])
    return res


    

async def status(request):
    res = await get_datasources_status(update_datasources_status(config[datasource_name]["tables"]["status"]))
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": None, 
        "data": res
        })




def dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')



def files_count(dirpath):
    return sum([len(files) for r, d, files in os.walk(dirpath)])




# async def parse_images(config, loop, executor):
#     path = os.path.join(config.RAW_DATA_PATH, "Takeout")

#     ins = await ParseGoogleImages(path, config)
#     await ins.parse()
#     images_data = ins.images_data

#     for image_data in images_data:
#         image_data.update({"tbl_object": config.IMAGES_TBL}) 
        

#     _, _ = await asyncio.wait(
#             fs=[loop.run_in_executor(executor, 
#                     functools.partial(q_images_db.store, **args)) for args in images_data],
#             return_when=asyncio.ALL_COMPLETED
#         )

#     for args in images_data:
#         await q_images_db.store(**args)

#     return 

# async def purchase_n_reservations(config, loop, executor):
#     path = os.path.join(config.RAW_DATA_PATH, "Takeout")

#     try:
#         ins = await PurchaseReservations(path, config)
#     except Exception as e:
#         logger.error(f"Parsing of purchases and reservations failed {e}")
#     reservations, purchases = await ins.parse()
    

#     for purchase in purchases:
#         purchase.update({"tbl_object": config.PURCHASES_TBL}) 

#     for reservation in reservations:
#         reservation.pop("products")
#         reservation.update({"tbl_object": config.RESERVATIONS_TBL}) 


#     # await asyncio.wait(
#     #         fs=[loop.run_in_executor(executor,  
#     #             functools.partial(q_purchase_db.store, **purchase)) for purchase in purchases],
#     #         return_when=asyncio.ALL_COMPLETED)
#     for purchase in purchases:
#         await q_purchase_db.store(**purchase)
    
#     # await asyncio.wait(
#     #         fs=[loop.run_in_executor(executor,  
#     #             functools.partial(q_reservation_db.store, **reservation)) for reservation in reservations],
#     #         return_when=asyncio.ALL_COMPLETED)
    
#     for reservation in reservations:
#         await q_reservation_db.store(**reservation)
    



#     return 


# async def asyncparse_takeout(config, loop, executor):
#     ##add this if this has to executed periodically
#     ##while True:
#     logger.info('Periodic task has begun execution')

#     instance = TakeoutEmails(config)

#     await asyncio.gather(*[
#                 instance.download_emails(loop, executor), 
#                 parse_images(config, loop, executor),
#                 purchase_n_reservations(config, loop, executor)
#                 ])

#     logger.info('Periodic task has finished execution')

    
#     return 


# # async def broadcast(config, message):
# #     broadcast = config.SIO.emit("takeout_response", {'data': message }, namespace="/takeout")

# #     #broadcasts = [ws.send(message) for ws in app.ws_clients]
# #     #for result in asyncio.as_completed(broadcasts):
# #     try:
# #         await asyncio.wait(broadcast)
# #         logger.info(f"completed {message}")
    
# #     except Exception as ex:
# #         template = f"An exception of type {ex} occurred"
# #         logger.error(template)
# #     return 




async def __parse(config, path, username):
    """

    datasource_name: This will be Google in this case, always

    """
    ##add this if this has to executed periodically
    ##while True:

    logger.info('Periodic task has begun execution')
    dst_path_prefix = os.path.join(config.RAW_DATA_PATH, DATASOURCE_NAME) 

    checksum, dest_path = await extract(path, dst_path_prefix, config, DATASOURCE_NAME, username)


    path = os.path.join(config.RAW_DATA_PATH, "Takeout")
    email_parsing_instance = await EmailParse(config, dest_path, username, checksum)
    await email_parsing_instance.download_emails()
    
    
    ins = ParseGoogleImages(config, dest_path, username, checksum)
    await ins.parse()
    
    res = {"message": "PROGRESS", "percentage": 98}
    await config["send_sse_message"](config, DATASOURCE_NAME, res)

    ins = await PurchaseReservations(config, dest_path, username, checksum)
    await ins.parse()

    # for purchase in purchases:
    #     purchase.update({"tbl_object": config.PURCHASES_TBL}) 
    #     await q_purchase_db.store(**purchase)

    # for reservation in reservations:
    #     reservation.pop("products")
    #     reservation.update({"tbl_object": config.RESERVATIONS_TBL}) 
    #     await q_reservation_db.store(**reservation)
        
    # logger.info('Periodic task has finished execution')

    res = {"message": "PROGRESS", "percentage": 100}
    await config["send_sse_message"](config, DATASOURCE_NAME, res)

    # ##updating datasources table with the status that parsing of the takeout is completed
    logger.info("Trying to update data source table with status completed")

    # email_parsing_instance.update_datasource_table("COMPLETED", email_parsing_instance.email_count)
    update_datasources_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "COMPLETED")
    
    takeout_dir = os.path.join(config["RAW_DATA_PATH"], DATASOURCE_NAME)
    username_paths = glob(f"{takeout_dir}/*")


    # usernames = [{"username": x[0], "path": os.path.join(datasource_dir, x[0])} for x in os.walk(datasource_dir)]
    for path in username_paths:
        size = dir_size(path)
        data_items = files_count(path) 
        logger.success(f"username == {path} size == {size} dataitems == {data_items}")

        await update_stats(config[DATASOURCE_NAME]["tables"]["stats_table"], 
                  GITHUB_DATASOURCE_NAME, 
                    username, data_items, size, "weekly", "auto", datetime.datetime.utcnow() + datetime.timedelta(days=7) ) 


    return 






async def parse(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path", "username"], request.json)

    # config = request.app.config
    # dst_path_prefix = os.path.join(config.RAW_DATA_PATH, DATASOURCE_NAME) 
    # logger.info(f"The dst_path_prefix fo rthis datasource is {dst_path_prefix}")
    
    # checksum, dest_path = await extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, request.json["username"])


    # request.app.add_task(extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, request.json["username"]))


    request.app.add_task(__parse(request.app.config, request.json["path"], request.json["username"]))


    # request.app.add_task(parse_takeout(request.app.config))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Takeout data parsing has been Started and you will be notified once it is complete", 
        "data": None
        })





async def reservation_filter(request):
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


@aiomisc.threaded
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


async def image_filter(request):

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



    images, count = await filter_images(request.app.config[DATASOURCE_NAME]["tables"]["image_table"], start_date, end_date, int(skip), int(limit))
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



async def attachment_filter(request):
    """
    To get all the assets created by the requester
    """
    logger.info(f"Args are {request.args.items()}")
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 50][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    message_type = request.args.get("message_type")
    matching_string = request.args.get("match_string") 

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

    if not matching_string:
        attachments, count = await filter_attachments(request.app.config[DATASOURCE_NAME]["tables"]["email_attachment_table"], message_type, start_date, end_date, int(skip), int(limit))
    else:
        raise APIBadRequest("Not been implemented Yet")
    # for iage in images:
    #     creation_time = image.pop("creation_time")
    #     #data:image/png;base64
    #     image.update({"creation_time": creation_time.strftime("%Y-%m-%d")})

    logger.success(attachments)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"result": attachments, "count": count},
        "message": None
        })



def format_purchase(config, db_purchase_obj):
    """
    db_purchase_obj: retrived from the db
    """
    logger.info(db_purchase_obj)
    products = json.loads(db_purchase_obj["products"])
    return {
            "merchant_name": db_purchase_obj["merchant_name"],
            "products": products,
            "time": db_purchase_obj["time"]
    }


async def purchases_filter(request):

    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    merchant_name = request.args.get("merchant_name") 

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



    purchases, count = await filter_purchases(request.app.config[DATASOURCE_NAME]["tables"]["purchase_table"], start_date, end_date, int(skip), int(limit), merchant_name)

    #result = [format_purchase(request.app.config, purchase) for purchase in purchases] 

    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"purchases": purchases, "count": count},
        'message': None
        })


async def reservations_filter(request):

    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    src = request.args.get("src") 
    dest = request.args.get("dest") 

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



    reservations, count = await filter_reservations(request.app.config[DATASOURCE_NAME]["tables"]["purchase_table"], start_date, end_date, int(skip), int(limit), src, dest)

    #result = [format_purchase(request.app.config, purchase) for purchase in purchases] 

    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"reservations": reservations, "count": count},
        'message': None
        })












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

    if not message_type:
        raise APIBadRequest("message type is required")

    # logger.info(f"Message type is {message_type}")
    # logger.info(f"Skip type is {skip}")
    # logger.info(f"limit type is {limit}")
    # logger.info(f"start date type is {start_date}, and type is {type(start_date)}")

    logger.info(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    # logger.info(f"This is the start_date {start_date}")
    # logger.info(f"This is the end_date {end_date}")


    if matching_string:
        emails, count = await match_text(request.app.config[DATASOURCE_NAME]["tables"]["email_table"], request.app.config[DATASOURCE_NAME]["tables"]["email_content_table"], \
                matching_string, message_type, start_date, end_date, int(skip), int(limit))
    else:
        logger.info("Without matching string")
        emails, count = await get_emails(request.app.config[DATASOURCE_NAME]["tables"]["email_table"], message_type, start_date, end_date, int(skip), int(limit))


    # emails = await get_emails(request.app.config.EMAILS_TBL, page, number, message_type)
    for email in emails:
        creation_time = email.pop("date")
        #data:image/png;base64
        email.update({"date": creation_time.strftime("%d %b, %Y")})

    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"emails": emails, "count": count},
        "message": None
        })



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
    

