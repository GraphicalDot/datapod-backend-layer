import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
from errors_module.errors import APIBadRequest
from .utils import _parse
from loguru import logger
import json
import base64
from io import BytesIO
from PIL import Image
import datetime
from .db_calls import update_status, update_stats, filter_tweet, \
        match_text, get_account, store, get_stats, get_status, get_archives
import dateparser

from .variables import DATASOURCE_NAME

from datasources.shared.extract import extract




async def stats(request):
    res = await get_stats(request.app.config[DATASOURCE_NAME]["tables"]["stats_table"])
    return res



async def status(request):
    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])
    return res

async def archives(request):
    res = await get_archives(request.app.config[DATASOURCE_NAME]["tables"]["archives_table"])
    return res



async def dashboard(request):
    res = await get_account(request.app.config[DATASOURCE_NAME]["tables"]["account_table"])

    result = res[0]
    result.update({"common_hashtags":  json.loads(result["common_hashtags"]), "common_user_mentions": json.loads(result["common_user_mentions"])})  


    return response.json(
        {
        'error': False,
        'success': True,
        'data': result, 
        "message": None
        })


async def parse(request):
    """
    To get all the assets created by the requester
    """
    
    request.app.config.VALIDATE_FIELDS(["path", "username"], request.json)


    username = request.json["username"].lower()
    config = request.app.config
    dst_path_prefix = os.path.join(config.RAW_DATA_PATH, DATASOURCE_NAME) 
    logger.info(f"The dst_path_prefix fo rthis datasource is {dst_path_prefix}")
    
    checksum, dest_path = await extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, username)
    

    request.app.add_task(_parse(request.app.config, dest_path, username, checksum))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Twitter parsing has been Started and you will be notified once it is complete", 
        "data": None
        })




async def tweets(request):

    logger.info("Number is ", request.args.get("limit"))
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    matching_string = request.args.get("match_string") 
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


    if matching_string:
        logger.info(f"THis is the matchiing_String {matching_string}")
        result, count = await match_text(request.app.config[DATASOURCE_NAME]["tables"]["tweet_table"], 
            request.app.config[DATASOURCE_NAME]["tables"]["indexed_tweet_table"], \
                
            matching_string , start_date, end_date,  int(skip), int(limit))

    else:

        result, count = await filter_tweet(request.app.config[DATASOURCE_NAME]["tables"]["tweet_table"], start_date, end_date, int(skip), int(limit))
    
    # [repo.update({
    #         "created_at":repo.get("created_at").strftime("%d, %b %Y"),
    #     }) for repo in result]

    return response.json(
        {
        'error': False,
        'success': True,
        'data': {"tweets": result, "count": count},
        'message': None
        })
    


