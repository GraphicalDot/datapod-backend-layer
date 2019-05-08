
#-*- coding:utf-8 -*- 


import subprocess
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .database_calls import create_db_instance, close_db_instance, get_key, insert_key, RetrieveInChunks

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
DATABASE_BP = Blueprint("database", url_prefix="/database")


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise Exception("Improper JSON format")





async def periodic(app, gmail_takeout_path):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')

    await asyncio.sleep(10)
    instance = GmailsEMTakeout(gmail_takeout_path, app.config.user_data_path, app.config.db_dir_path)
    instance.download_emails()
    logger.info('Periodic task has finished execution')
    return 

@DATABASE_BP.get('/logs')
async def get_logs(request):
    """
    To get all the assets created by the requester
    """
    db_instance = create_db_instance(request.app.config.db_dir_path)
    stored_value = get_key("logs", db_instance)

    if not stored_value:
        stored_value = []
    close_db_instance(db_instance)


    
    return response.json(
        {
        'error': False,
        'success': True,
        "data": stored_value
        })


@DATABASE_BP.get('/stats')
async def get_all_stats(request):
    """
    To get all the assets created by the requester
    """
    def du(path):
        """disk usage in human readable format (e.g. '2,1GB')"""
        return subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')

    number_of_files = sum([len(files) for r, d, files in os.walk(request.app.config.user_data_path)])
    total_size = du(request.app.config.user_data_path)
    services = [
            {"service": "gmail",  "username": "houier.saurav@gmail.com", "last_updated": "2019-04-29 15:49:56 IST+0530"},
            {"service": "instagram",  "username": "sauravverma86", "last_updated": "2019-04-28 12:12:56 IST+0530"}

    ]

    
    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"services": services, "files": number_of_files, "size": total_size}
        })


@DATABASE_BP.get('/images/instagram')
async def get_insta_images(request):
    """
    To get all the assets created by the requester
    """
    db_instance = create_db_instance(request.app.config.db_dir_path)
    stored_value = get_key("instagram_images", db_instance)

    if not stored_value:
        stored_value = []
    close_db_instance(db_instance)

    logger.info(stored_value)
    result = []
    for image in stored_value:
        file_path = f"file:/{image['path']}"
        image.update({"file_path": file_path})


    return response.json(
        {
        'error': False,
        'success': True,
        "data": stored_value
        })

import base64

@DATABASE_BP.get('/images/facebook')
async def get_facebook_images(request):
    """
    """
    db_instance = create_db_instance(request.app.config.db_dir_path)
    stored_value = get_key("facebook_images", db_instance)

    if not stored_value:
        stored_value = []
    close_db_instance(db_instance)

    
    for e in stored_value:
        ext = e["uri"].split(".")[-1]
        with open(e["uri"], "rb") as f:
            _img = base64.b64encode(f.read())
            img_source = 'data:image/%s;base64,'%ext+_img.decode()
        
        number = e.get("comments") 
        if number:
            e.update({"comments": len(number)})
        else:
            e.update({"comments": 0})
        e.update({"uri": img_source})
        e.pop("media_metadata")
        e.pop("title")


    # var _img = fs.readFileSync(img).toString('base64')
    # this.img_source = 'data:image/png;base64,'+_img

    logger.info(stored_value)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": stored_value
        })


@DATABASE_BP.get('/images/gmail')
async def get_gmail_images(request):
    """
    Right now indexing is not available
    """
    db_instance = create_db_instance(request.app.config.db_dir_path)
    
    ins_normal = RetrieveInChunks("gmail", db_instance, "gmail_images_normal", 1)

    result_normal = ins_normal.retreive()

    ins_png = RetrieveInChunks("gmail", db_instance, "gmail_images_png", 1)
    result_png = ins_png.retreive()

    images = result_normal
    for image in result_normal:
        ext = image["path"].split(".")[-1]
        with open(image["path"], "rb") as f:
            _img = base64.b64encode(f.read())
            img_source = 'data:image/%s;base64,'%ext+_img.decode()
        image.update({"uri": img_source})

    for image in result_png:
        with open(image["path"], "rb") as f:
            _img = base64.b64encode(f.read())
            img_source = 'data:image/png;base64,'+_img.decode()
        image.update({"uri": img_source})


    close_db_instance(db_instance)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": result_normal+result_png
        })


@DATABASE_BP.get('/gmail/purchases')
async def get_gmail_purchases(request):
    """
    Right now indexing is not available
    """
    db_instance = create_db_instance(request.app.config.db_dir_path)
    stored_value = get_key("gmail_purchase", db_instance)
    
    close_db_instance(db_instance)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": stored_value
        })


@DATABASE_BP.get('/gmail/reservations')
async def get_gmail_reservations(request):
    """
    Right now indexing is not available
    """
    db_instance = create_db_instance(request.app.config.db_dir_path)
    stored_value = get_key("gmail_reservations", db_instance)
    logger.info(stored_value)
    close_db_instance(db_instance)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": stored_value
        })

