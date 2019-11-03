import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from .utils import __parse
from errors_module.errors import APIBadRequest
from loguru import logger
import json
import base64
from io import BytesIO
from PIL import Image
from datasources.shared.extract import extract
from .db_calls import get_stats, get_status, filter_chats, filter_images, dashboard_data
from .variables import DATASOURCE_NAME
import subprocess

import dateparser

async def stats(request):
    res = await get_stats(request.app.config[DATASOURCE_NAME]["tables"]["stats_table"])
    return res


    

async def status(request):
    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])
    return res





async def dashboard(request):

    username = request.args.get("username")
    if not username:
        raise APIBadRequest("username is required")
    
    res = await dashboard_data(username, request.app.config[DATASOURCE_NAME]["tables"]["image_table"], 
                    request.app.config[DATASOURCE_NAME]["tables"]["chat_table"], 
                    request.app.config[DATASOURCE_NAME]["tables"]["address_table"])

    return response.json(
        {
        'error': False,
        'success': True,
        "message": None ,
        "data": res
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
                raise APIBadRequest("Already processing a facebook for the user")




    config = request.app.config
    dst_path_prefix = os.path.join(config.RAW_DATA_PATH,DATASOURCE_NAME) 
    logger.info(f"The dst_path_prefix fo rthis datasource is {dst_path_prefix}")
    
    checksum, dest_path = await extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, request.json["username"])
    
    request.app.add_task(__parse(request.app.config, dest_path, request.json["username"], checksum))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Facebook data parsing has been Started and you will be notified once it is complete", 
        "data": None
        })



def image_base64(path):
    try:
        image = Image.open(path)
        buffered = BytesIO()
        image.save(buffered, format=image.format)
        img_str = base64.b64encode(buffered.getvalue())
    except Exception as e:
        logger.error(f"Error {e} while converting fb image to base64")
    return img_str.decode()


async def get_chats(request):

    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    username = request.args.get("username")
    if not username:
        raise APIBadRequest("username is required")

    search_text = request.args.get("search_text")

    if search_text:
        search_text = search_text.lower()
    logger.info(request.args)

    if not username:
        raise APIBadRequest("Username for this datasource is required")



    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")


    _chats, count = await filter_chats(request.app.config[DATASOURCE_NAME]["tables"]["chat_table"], username, start_date, end_date, int(skip), int(limit), search_text)

    for chat in _chats:
        chat.pop("message_content")
        chat.pop("chat_path")
        if chat.get("messages"):
            messages = json.loads(chat.get("messages"))
            chat.update({"messages": messages})

            ##we need to give one message to frontend, We need to loop over messages till the time 
            ## we get a message which is not None, then break the loop
            for message in  messages:
                if message.get("content"):
                    chat.update({"last_message": message.get("content")})
                    break

        if chat.get("participants"):
            participants = json.loads(chat.get("participants"))
            chat.update({"participants": participants})



    return response.json(
        {
        'error': False,
        'success': True,
        "message": None, 
        "data": {"chats": _chats, "count": count}
        })





# @FACEBOOK_BP.get('/images')
async def images(request):

    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    username = request.args.get("username")
    
    logger.info(request.args)

    if not username:
        raise APIBadRequest("Username for this datasource is required")



    if start_date:
        start_date = dateparser.parse(start_date)


    if end_date:
        end_date = dateparser.parse(end_date)


    if start_date and end_date:
        if end_date < start_date:
            raise APIBadRequest("Start date should be less than End date")

    logger.info(f"This is the start_date {start_date}")
    logger.info(f"This is the end_date {end_date}")

    logger.info(f'Name of the Facebook Table {request.app.config[DATASOURCE_NAME]["tables"]["image_table"]}')

    images, count = await filter_images(request.app.config[DATASOURCE_NAME]["tables"]["image_table"], username, start_date, end_date, int(skip), int(limit))


    for image_data in images:
        logger.info(image_data)
        path = image_data['uri']
        logger.info(path)
        encoded_string = "data:image/jpeg;base64," + image_base64(path)
            
        if image_data.get("comments"):
            comments = json.loads(image_data.get("comments"))
            image_data.update({"comments": comments})
        
        image_data.update({"path": path, "uri": encoded_string, "creation_timestamp": image_data["creation_timestamp"].strftime("%d %b, %Y")})


    return response.json(
        {
        'error': False,
        'success': True,
        "message": None, 
        "data": {"images": images, "count": count}
        })


# @FACEBOOK_BP.get('/chat')
async def single_chat(request):
    """
    To get all the chats created by the user
    thread_path = 'inbox/KapilDevGarg_lapjbN90Hw'
    """


    thread_path = request.args.get("thread_path")
    if not thread_path:
        raise APIBadRequest("thread_path  is required")
    
    logger.info(f'This is the chat id {request.args.get("chat_id")}')
    ds_path = os.path.join(request.app.config.RAW_DATA_PATH, f"facebook/messages/{thread_path}")

    if not os.path.exists(ds_path):
        raise APIBadRequest("This thread_path doesnt exists")

    logger.info(ds_path)
    chats = []
    chat_files= [(os.path.join(ds_path, file)) for file in os.listdir(ds_path)]
    for _file in chat_files:
        with open(_file, "r") as json_file:   
            data = json.load(json_file)
            logger.info(data)
            chats.extend(data.get("messages"))
    # if request.json.get("message_type") not in chat_types:
    #     raise APIBadRequest("This message type is not available")


    # chat_path = os.path.join(ds_path, request.json.get("message_type"))

    # all_chats = os.listdir(chat_path)
    # result = [{"name": e.split("_")[0], "chat_id": e} for e in all_chats]

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Facebook data parsing has been Started and you will be notified once it is complete", 
        "data": chats
        })
