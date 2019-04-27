#-*- coding:utf-8 -*- 



import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import coloredlogs, verboselogs, logging
import os
from errors_module.errors import APIBadRequest

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



@GMAIL_BP.post('/takeout')
async def gmail_takeout(request):
    """
    To get all the assets created by the requester
    """
    required_fields = ["path"]
    validate_fields(required_fields, request.json)
    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")


    return response.json(
        {
        'error': False,
        'success': True,
        })
