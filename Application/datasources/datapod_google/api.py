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
import calendar
# import  database_calls.db_purchases as q_purchase_db
# import  database_calls.db_reservations as q_reservation_db
# import  database_calls.db_images as q_images_db
# from   database_calls.takeout.db_emails  import match_text as e_match_text
# from database_calls.takeout.db_emails  import  get_email_attachment, get_emails, match_text


import shutil
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
import subprocess
from loguru import logger
from datasources.shared.extract import extract
import aiomisc
from .utils.location import LocationHistory
from .db_calls import update_status, get_emails, match_text, filter_images, filter_locations,\
         filter_attachments, filter_purchases, filter_reservations, get_stats, get_status, \
             update_stats, delete_status, update_percentage, filter_attachments_on_text, delete_archive
from .variables import DATASOURCE_NAME, DEFAULT_SYNC_TYPE, DEFAULT_SYNC_FREQUENCY




async def stats(request):
    res = await get_stats(request.app.config[DATASOURCE_NAME]["tables"]["stats_table"])
    return res


    

async def status(request):
    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])
    return res




def dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')



def files_count(dirpath):
    return sum([len(files) for r, d, files in os.walk(dirpath)])




async def restart_parse(request):
    request.app.config.VALIDATE_FIELDS(["username"], request.json)

    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"], request.json["username"])

    result = list(res)
    if not result:
        raise APIBadRequest(f"No status present for {DATASOURCE_NAME} for username {request.json['username']}")


    result = result[0]
    original_path = result.get("original_path")

    if not original_path:
        raise APIBadRequest(f"No Path is present for {DATASOURCE_NAME} for username {request.json['username']}, Please cancel this processing")

    if not os.path.exists(original_path):
        raise APIBadRequest(f"This path {original_path} doesnts exists anymore, Please cancel this processing")

    request.app.add_task(start_parse(request.app.config, original_path, request.json["username"]))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Takeout data parsing for {request.json['username']} has been restarted and you will be notified once it is complete", 
        "data": None
        })



async def cancel_parse(request):
    request.app.config.VALIDATE_FIELDS(["username"], request.json)


    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"], request.json['username'])

    result = list(res)
    if not result:
        raise APIBadRequest(f"No status present for {DATASOURCE_NAME} for username {request.json['username']}")


    result = result[0]
    datapod_path = result.get("path")
    checksum = result.get("checksum")
    logger.warning(f"{datapod_path} will be deleted with {checksum}")
    ##deleting entry from the status table corresponding to this username
    try:    
        shutil.rmtree(datapod_path)
        logger.success(f"{datapod_path} is deleted now")
    except Exception as e:
        return response.json(
            {
            'error': False,
            'success': True,
            "message": f"Path at {datapod_path} couldnt be delete because of {e.__str__()}", 
            "data": None
            })

    await delete_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, request.json['username'])
    await delete_archive(request.app.config[DATASOURCE_NAME]["tables"]["archives_table"], checksum)
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": f"Processing for {request.json['username']} has been cancelled and all resources have been freed", 
        "data": None
        })
    






async def start_parse(config, path, username):
    """

    datasource_name: This will be Google in this case, always

    """
    ##add this if this has to executed periodically
    ##while True:

    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "PROGRESS")


    logger.debug('Periodic task has begun execution')
    dst_path_prefix = os.path.join(config.RAW_DATA_PATH, DATASOURCE_NAME) 



    ##the dest_path is the path with the archieve appended to the last
    try:
        checksum, dest_path = await extract(path, dst_path_prefix, config, DATASOURCE_NAME, username)
        await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "PROGRESS", checksum, dest_path, path)

    except Exception as e:
        logger.error(e)
        await delete_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username)
        raise Exception(e)

    # path = os.path.join(config.RAW_DATA_PATH, "Takeout")
    email_parsing_instance = await EmailParse(config, dest_path, username, checksum)
    if not email_parsing_instance:
        logger.error("Takeout path doesnt exists")

    if len(email_parsing_instance.mbox_file_names) != 0:
        await email_parsing_instance.download_emails()
    else:
        logger.error("There is no mbox file present in the datasource ")
    
    try:
        ins = ParseGoogleImages(config, dest_path, username, checksum)
        await ins.parse()
    except Exception as e:
        logger.error(e)

    res = {"message": "PROGRESS", "percentage": 98}
    await update_percentage(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, 98)

    await config["send_sse_message"](config, DATASOURCE_NAME, res)

    try:
        ins = await PurchaseReservations(config, dest_path, username, checksum)
        await ins.parse()
    except Exception as e:
        logger.error(e)


    try:
        ins = LocationHistory(config, dest_path, username, checksum)
        await ins.parse()
    except Exception as e:
        logger.error(e)


    # for purchase in purchases:
    #     purchase.update({"tbl_object": config.PURCHASES_TBL}) 
    #     await q_purchase_db.store(**purchase)

    # for reservation in reservations:
    #     reservation.pop("products")
    #     reservation.update({"tbl_object": config.RESERVATIONS_TBL}) 
    #     await q_reservation_db.store(**reservation)
        
    # logger.debug('Periodic task has finished execution')

    res = {"message": "PROGRESS", "percentage": 100}
    await config["send_sse_message"](config, DATASOURCE_NAME, res)
    await update_percentage(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, res["percentage"])

    # ##updating datasources table with the status that parsing of the takeout is completed
    logger.debug("Trying to update data source table with status completed")

    # email_parsing_instance.update_datasource_table("COMPLETED", email_parsing_instance.email_count)
    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "COMPLETED", checksum)
    
    takeout_dir = os.path.join(config["RAW_DATA_PATH"], DATASOURCE_NAME, username)


    # usernames = [{"username": x[0], "path": os.path.join(datasource_dir, x[0])} for x in os.walk(datasource_dir)]
    size = dir_size(takeout_dir)
    data_items = files_count(takeout_dir) 
    logger.success(f"username == {takeout_dir} size == {size} dataitems == {data_items}")

    await update_stats(config[DATASOURCE_NAME]["tables"]["stats_table"], 
                DATASOURCE_NAME, 
                username, data_items, size, DEFAULT_SYNC_FREQUENCY, DEFAULT_SYNC_TYPE, datetime.datetime.utcnow() + datetime.timedelta(days=7) ) 

    logger.success(f"Parsing for Takeout {username} is completed")

    return 


async def delete_original_path(request):
    """
    After the processing of the whole data source, this api can be used to delete the original zip 
    correspoding to a particular username
    """
    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"], username)

    result = list(res)
    logger.debug(result[0].get("username"))
    if not result:
        raise APIBadRequest(f"No status present for {DATASOURCE_NAME} for username {username}")


    result = result[0]
    logger.debug(result)
    path_to_be_deleted = result.get("original_path")
    logger.warning(f"Path to be deleted is {path_to_be_deleted}")

    try:    
        os.remove(path_to_be_deleted)
        logger.success(f"{path_to_be_deleted} is deleted now")
    except Exception as e:
        return response.json(
            {
            'error': False,
            'success': True,
            "message": f"Original path at {path_to_be_deleted} couldnt be delete because of {e.__str__()}", 
            "data": None
            })


    return response.json(
        {
        'error': False,
        'success': True,
        "message": f"Original path at {path_to_be_deleted} is deleted", 
        "data": None
        })



async def parse(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path", "username"], request.json)

    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])
    res = list(res)
    logger.debug(res)
    if res:
        for element in res:
            if element.get("status") == "PROGRESS":
                raise APIBadRequest("Already processing a Takeout account for the user")




    # config = request.app.config
    # dst_path_prefix = os.path.join(config.RAW_DATA_PATH, DATASOURCE_NAME) 
    # logger.debug(f"The dst_path_prefix fo rthis datasource is {dst_path_prefix}")
    
    # checksum, dest_path = await extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, request.json["username"])


    # request.app.add_task(extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, request.json["username"]))


    request.app.add_task(start_parse(request.app.config, request.json["path"], request.json["username"]))


    # request.app.add_task(parse_takeout(request.app.config))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": f"Takeout data parsing has been Started for {request.json['username']} and you will be notified once it is complete", 
        "data": None
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

    logger.debug("Number is ", request.args.get("limit"))
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    logger.debug(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")




    images, count = await filter_images(request.app.config[DATASOURCE_NAME]["tables"]["image_table"], username, start_date, end_date, int(skip), int(limit))
    logger.debug(images)
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
    logger.debug(f"Args are {request.args.items()}")
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 50][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    message_type = request.args.get("message_type")
    matching_string = request.args.get("match_string") 
    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    # logger.debug(f"Skip type is {skip}")
    # logger.debug(f"limit type is {limit}")
    # logger.debug(f"start date type is {start_date}, and type is {type(start_date)}")

    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")


    if not matching_string:
        attachments, count = await filter_attachments(request.app.config[DATASOURCE_NAME]["tables"]["email_attachment_table"], 
                                    username,  message_type, start_date, end_date, int(skip), int(limit))
    else:
        attachments, count = await filter_attachments_on_text(request.app.config[DATASOURCE_NAME]["tables"]["email_attachment_table"], 
                            username,  message_type, start_date, end_date, int(skip), int(limit), matching_string)
    # for iage in images:
    #     creation_time = image.pop("creation_time")
    #     #data:image/png;base64
    #     image.update({"creation_time": creation_time.strftime("%Y-%m-%d")})

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
    merchant_name = request.args.get("match_string") 
    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    logger.debug(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    # logger.debug(f"This is the start_date {start_date}")
    # logger.debug(f"This is the end_date {end_date}")



    purchases, count = await filter_purchases(request.app.config[DATASOURCE_NAME]["tables"]["purchase_table"], username,  start_date, end_date, int(skip), int(limit), merchant_name)

    result = [format_purchase(request.app.config, purchase) for purchase in purchases] 
    
    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"purchases": result, "count": count},
        'message': None
        })

async def reservations_filter(request):

    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    search_text = request.args.get("match_string") 

    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    logger.debug(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")




    reservations, count = await filter_reservations(request.app.config[DATASOURCE_NAME]["tables"]["reservation_table"], username,  start_date, end_date, int(skip), int(limit), search_text)

    #result = [format_purchase(request.app.config, purchase) for purchase in purchases] 

    result = list(reservations)

    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"reservations": result, "count": count},
        'message': None
        })



    

async def locations_filter(request):
    logger.debug(f"Args are {request.args.items()}")

    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    logger.debug(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)
        start_date = calendar.timegm(start_date.timetuple())

    if end_date:
        end_date = dateparser.parse(end_date)
        end_date  = calendar.timegm(end_date.timetuple())

    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")




    locations, count = await filter_locations(request.app.config[DATASOURCE_NAME]["tables"]["location_approximate_table"], username,  start_date, end_date)
    logger.debug(locations)
    #result = [format_purchase(request.app.config, purchase) for purchase in purchases] 

    result = list(locations)

    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"locations": result, "count": count},
        'message': None
        })







async def emails_filter(request):
    """
    To get all the assets created by the requester
    """

    logger.debug(f"Args are {request.args.items()}")
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 50][request.args.get("limit") == None] 
    matching_string = request.args.get("match_string") 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    message_type = request.args.get("message_type")
    username = request.args.get("username") 
    attachments = request.args.get("attachments")
    
    logger.debug(f"Value of attachments arg in get request <<{attachments}>> and {bool(attachments)}")
    if attachments:
        attachments = bool(attachments)

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    if not message_type:
        raise APIBadRequest("message type is required")

    # logger.debug(f"Message type is {message_type}")
    # logger.debug(f"Skip type is {skip}")
    # logger.debug(f"limit type is {limit}")
    # logger.debug(f"start date type is {start_date}, and type is {type(start_date)}")

    logger.debug(f"Params are {request.args}")
    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    # logger.debug(f"This is the start_date {start_date}")
    # logger.debug(f"This is the end_date {end_date}")

    logger.debug(f"This is the matching string {matching_string}")
    
    if matching_string:

        emails, count = await match_text(request.app.config[DATASOURCE_NAME]["tables"]["email_table"], username,  request.app.config[DATASOURCE_NAME]["tables"]["email_content_table"], \
                matching_string, message_type, start_date, end_date, int(skip), int(limit), attachments)
    else:
        logger.debug("Without matching string")
        emails, count = await get_emails(request.app.config[DATASOURCE_NAME]["tables"]["email_table"], username,  message_type, start_date, end_date, int(skip), int(limit), attachments)


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
    

