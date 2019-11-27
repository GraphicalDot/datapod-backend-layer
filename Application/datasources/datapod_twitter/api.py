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
        match_text, get_account, store, get_stats, get_status, get_archives, delete_status, delete_archive
import dateparser

from .variables import DATASOURCE_NAME, DEFAULT_SYNC_TYPE, DEFAULT_SYNC_FREQUENCY

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

    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

    res = await get_account(request.app.config[DATASOURCE_NAME]["tables"]["account_table"], username)

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

    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])

    res = list(res)
    logger.info(res)
    if res:
        for element in res:
            if element.get("status") == "PROGRESS":
                raise APIBadRequest("Already processing a twitter for the user")

    username = request.json["username"].lower()
    config = request.app.config
    dst_path_prefix = os.path.join(config.RAW_DATA_PATH, DATASOURCE_NAME) 
    logger.info(f"The dst_path_prefix fo rthis datasource is {dst_path_prefix}")
    
    try:
        checksum, dest_path = await extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, username)
        await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "PROGRESS", checksum, dest_path, request.json["path"])

    except Exception as e:
        logger.error(e)
        await delete_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username)
        raise APIBadRequest(e)

    request.app.add_task(_parse(request.app.config, dest_path, username, checksum))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Twitter parsing has been Started and you will be notified once it is complete", 
        "data": None
        })



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
    logger.info(result[0].get("username"))
    if not result:
        raise APIBadRequest(f"No status present for {DATASOURCE_NAME} for username {username}")


    result = result[0]
    logger.info(result)
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


async def tweets(request):

    logger.info("Number is ", request.args.get("limit"))
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    matching_string = request.args.get("match_string") 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    username = request.args.get("username") 

    if not username:
        raise APIBadRequest("Username for this datasource is required")

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
            username, 
            request.app.config[DATASOURCE_NAME]["tables"]["indexed_tweet_table"], \
                
            matching_string , start_date, end_date,  int(skip), int(limit))

    else:

        result, count = await filter_tweet(request.app.config[DATASOURCE_NAME]["tables"]["tweet_table"], username, start_date, end_date, int(skip), int(limit))
    
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
    


