#-*- coding:utf-8 -*- 



import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .gmail_takeout import GmailsEMTakeout

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

    if not request.json["path"].endswith("mbox"):
        raise APIBadRequest("This path is not a valid mbox file")


    logger.info(f"THe request was successful with path {request.json['path']}")
    
    request.app.add_task(periodic(request.app, request.json["path"]))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
        })
