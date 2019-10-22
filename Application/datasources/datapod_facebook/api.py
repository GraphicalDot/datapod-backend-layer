import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from .utils import __parse
from errors_module.errors import APIBadRequest
from loguru import logger
from .db_calls import filter_images
import json
import base64
from io import BytesIO
from PIL import Image
from datasources.shared.extract import extract
from .db_calls import get_stats, get_status
from .variables import DATASOURCE_NAME
import subprocess


async def stats(request):
    res = await get_stats(request.app.config[DATASOURCE_NAME]["tables"]["stats_table"])
    return res


    

async def status(request):
    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])
    return res










async def parse(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path", "username"], request.json)

    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])

    if res:
        if res.get("status") == "PROGRESS":
            raise APIBadRequest("Already processing a facebook account for the user")




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


# @FACEBOOK_BP.get('/images')
async def images(request):

    logger.info("Number is ", request.args.get("limit"))
    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 10][request.args.get("limit") == None] 
    start_date = request.args.get("start_date") 
    end_date = request.args.get("end_date") 
    username = request.args.get("username")

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

    logger.info(f'Name of the Facebook Table {request.app.config[DATASOURCE_NAME]["tables"]["image_table"]}')

    images, count = await filter_images(request.app.config[DATASOURCE_NAME]["tables"]["image_table"], start_date, end_date, int(skip), int(limit), username)


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

def read_chat(config, chat_type, chat_id, all_messages=False):

    ds_path = os.path.join(config.RAW_DATA_PATH, f"facebook/messages/{chat_type}/{chat_id}")

    result = {}

    chat_files= [os.path.join(ds_path, file) for file in os.listdir(ds_path) if os.path.isfile(os.path.join(ds_path, file))]


    if len(chat_files) > 0:
        #implies that only photos type of folder exists for this chat id and there is no message.json files
        with open(chat_files[0], "r") as json_file:   
            data = json.load(json_file)

            #extracting only one message out of all the messages
            messages = data["messages"][0]
            timestamp_ms = messages["timestamp_ms"]
            messages.update({"timestamp_ms": datetime.datetime.utcfromtimestamp(timestamp_ms/1000).strftime("%d %b, %Y")})

            result.update({"title": data["title"], "participants": data["participants"], "thread_type": data["thread_type"], 
                    "thread_path": data["thread_path"],  "messages": messages})    
    else:
        logger.error(f"No messages found for {chat_type} and {chat_id} {chat_files}" )
        return False

    chats = []
    if all_messages:
        for _file in chat_files:
            with open(_file, "r") as json_file:   
                data = json.load(json_file)
                chats.extend(data.get("messages"))

    return result    


# @FACEBOOK_BP.get('/chats')
async def allchats(request):
    """
    To get all the chats created by the user
    """
    #request.app.config.VALIDATE_FIELDS(["message_type"], request.json)
    ds_path = os.path.join(request.app.config.RAW_DATA_PATH, "facebook/messages")
    chat_types = os.listdir(ds_path)
    result = {}

    for chat_type in ["stickers_used"]:
        if chat_type in chat_types:
            chat_types.remove(chat_type)

    for chat_type in chat_types:
        ##this will be names type like archieved, inbox etc
        chat_type_path = os.path.join(ds_path, chat_type)

        all_chats = os.listdir(chat_type_path)
        #chat_ids = [{"name": e.split("_")[0], "chat_id": e} for e in all_chats]


        chats = []
        for chat_id in all_chats:
            chat_data = read_chat(request.app.config, chat_type, chat_id)
            if chat_data:
                chats.append(chat_data)


        result.update({chat_type: chats})


    # if request.json.get("message_type") not in chat_types:
    #     raise APIBadRequest("This message type is not available")



    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Facebook data parsing has been Started and you will be notified once it is complete", 
        "data": result
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
