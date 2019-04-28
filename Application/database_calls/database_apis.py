
#-*- coding:utf-8 -*- 



import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .database_calls import create_db_instance, close_db_instance, get_key, insert_key

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
