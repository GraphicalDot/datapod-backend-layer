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
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
GMAIL_BP = Blueprint("gmail", url_prefix="/gmail")


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise Exception("Improper JSON format")




@GMAIL_BP.post('/credentials')
async def gmail_login(request):
    """
    To get all the assets created by the requester
    """
    required_fields = ["username", "password"]
    validate_fields(required_fields, request.json)

    return response.json(
        {
        'error': False,
        'success': True,
        })


    ##add this if this has to executed periodically
    ##while True:

    password = "BIGzoho8681@#"
    key, salt = generate_scrypt_key(password)
    logging.info(f"salt for scrypt key is {salt}")
    logging.info(f" key for AES encryption is  {key}")

    for (source, destination, encrypted_path) in source_destination_list: 
        shutil.make_archive(destination, 'zip', source)
        logger.info(f"Archiving done at the path {destination}")
        time.sleep(1)
        with open("%s.zip"%destination, "rb") as f:
            file_bytes = f.read()
            data = aes_encrypt(key, file_bytes)
            with open(encrypted_path, "wb") as f:
                f.write(data)


    return 




async def periodic(app, gmail_takeout_path):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')

    await asyncio.sleep(10)
    instance = GmailsEMTakeout(gmail_takeout_path, app.config.user_data_path, app.config.db_dir_path)
    instance.download_emails()



    logger.info('Periodic task has finished execution')
    return 

@GMAIL_BP.post('/takeout')
async def gmail_takeout(request):
    """
    To get all the assets created by the requester
    """
    required_fields = ["path"]
    validate_fields(required_fields, request.json)
    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    # if not request.json["path"].endswith("mbox"):
    #     raise APIBadRequest("This path is not a valid mbox file")
    archive_file_name = os.path.basename(request.json["path"])

    if not os.path.exists(request.app.config.user_data_path):
            os.makedirs(request.app.config.user_data_path)

    
    path = os.path.join(request.app.config.user_data_path,   "Takeout/Mail/All mail Including Spam and Trash.mbox")
    
    if not os.path.exists(path):
        shutil.unpack_archive(request.json["path"], extract_dir=request.app.config.user_data_path, format=None)
    
    
    logger.info(f"THe request was successful with path {path}")
    
    request.app.add_task(periodic(request.app, path))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
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