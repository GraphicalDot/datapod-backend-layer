import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from .utils import __parse, update_datasource_table
from errors_module.errors import APIBadRequest
from loguru import logger
from .db_calls import filter_images
import json
import base64
from io import BytesIO
from PIL import Image
from datasources.shared.extract import extract

DATASOURCE_NAME = "Facebook"


# FACEBOOK_BP = Blueprint("facebook", url_prefix="/facebook")





# @FACEBOOK_BP.route('/serve')
# async def serve(request):
#     path = request.args.get("path")

#     request.app.url_for(path) 

# FACEBOOK_BP.static('/profile',  "~/.datapod/userdata/raw/facebook/photos_and_videos/Profilepictures_IHIxz3DIcQ/")


# @FACEBOOK_BP.post('/parse')
# async def parse(request):




async def stats(request):
    pass


async def status(request):
    pass



async def parse(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path", "username"], request.json)

    config = request.app.config
    dst_path_prefix = os.path.join(config.RAW_DATA_PATH,DATASOURCE_NAME) 
    logger.info(f"The dst_path_prefix fo rthis datasource is {dst_path_prefix}")
    
    checksum, dst_path = await extract(request.json["path"], dst_path_prefix, config, DATASOURCE_NAME, request.json["username"])
    



    # if not os.path.exists(request.json["path"]):
    #     raise APIBadRequest("This path doesnt exists")

    # try:
    #     the_zip_file = zipfile.ZipFile(request.json["path"])
    # except:
    #     raise APIBadRequest("Invalid zip takeout file")


    # logger.info(f"Testing zip {request.json['path']} file")
    # ret = the_zip_file.testzip()

    # if ret is not None:
    #     raise APIBadRequest("Invalid zip takeout file")

    # ##check if mbox file exists or not



    # logger.info("Copying and extracting facebook data")

    # ds_path = os.path.join(request.app.config.RAW_DATA_PATH, "facebook")
    # try:
    #     shutil.unpack_archive(request.json["path"], extract_dir=ds_path, format=None)
    # except:
    #     raise APIBadRequest("Invalid zip facebook file")

    # logger.info("Copying and extracting facebook data completed")





    request.app.add_task(__parse(request.app.config, ds_path))

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
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 20][request.args.get("number") == None] 
    result = await filter_images(request.app.config.FB_IMAGES_TBL , page, number)
    for image_data in result:

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
        "data": result
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
