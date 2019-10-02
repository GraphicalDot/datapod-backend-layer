import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
from errors_module.errors import APIBadRequest
from .twitter_ds import _parse
from loguru import logger
from database_calls.twitter.calls import filter_tweet, match_text, get_account
import json
import base64
from io import BytesIO
from PIL import Image
import datetime
from database_calls.credentials import update_datasources_status, datasource_status
import dateparser

TWITTER_BP = Blueprint("twitter", url_prefix="/twitter")





# @TWITTER_BP.route('/serve')
# async def serve(request):
#     path = request.args.get("path")

#     request.app.url_for(path) 

# TWITTER_BP.static('/profile',  "~/.datapod/userdata/raw/facebook/photos_and_videos/Profilepictures_IHIxz3DIcQ/")


# @TWITTER_BP.post('/parse')
# async def parse(request):



@TWITTER_BP.get('/dashboard')
async def dashboard(request):
    res = await get_account(request.app.config.TWITTER_ACC_TBL)



    return response.json(
        {
        'error': False,
        'success': True,
        'data': res,
        "message": None
        })


@TWITTER_BP.post('/parse')
async def parse(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path"], request.json)




    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    if not os.path.basename(request.json["path"]).startswith("twitter"):
        raise APIBadRequest("Invalid Twitter zip file")


    try:
        the_zip_file = zipfile.ZipFile(request.json["path"])
    except:
        raise APIBadRequest("Invalid Twitter zip file")


    logger.info(f"Testing zip {request.json['path']} file")
    ret = the_zip_file.testzip()

    if ret is not None:
        raise APIBadRequest("Invalid twitter zip file")

    ##check if mbox file exists or not



    logger.info("Copying and extracting zip data")

    ds_path = os.path.join(request.app.config.RAW_DATA_PATH, "twitter")
    try:
        shutil.unpack_archive(request.json["path"], extract_dir=ds_path, format=None)
    except:
        raise APIBadRequest("Invalid zip twitter file")

    logger.info("Copying and extracting facebook data completed")

    request.app.add_task(_parse(request.app.config, ds_path))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Twitter parsing has been Started and you will be notified once it is complete", 
        "data": None
        })




@TWITTER_BP.get("/tweets")
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
        result, count = await match_text(request.app.config.TWITTER_TBL, request.app.config.TWITTER_INDEXED_TBL, \
            matching_string , start_date, end_date,  int(skip), int(limit))

    else:

        result, count = await filter_tweet(request.app.config.TWITTER_TBL, start_date, end_date, int(skip), int(limit))
    
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
    



@TWITTER_BP.get("/messages")
async def messages(request):

    return response.json(
            {
            'error': False,
            'success': True,
            "message": None, 
            "data": []
            })


# @TWITTER_BP.get("/followers")
# async def followers(request):

#     return response.json(
#             {
#             'error': False,
#             'success': True,
#             "message": None, 
#             "data": []
#             })



# @TWITTER_BP.get("/following")
# async def following(request):

#     return response.json(
#             {
#             'error': False,
#             'success': True,
#             "message": None, 
#             "data": []
#             })




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


@TWITTER_BP.get('/chats')
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

@TWITTER_BP.get('/chat')
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
