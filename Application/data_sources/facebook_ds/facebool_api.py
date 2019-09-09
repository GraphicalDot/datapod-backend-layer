import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
from .facebook_ds import __parse, update_datasource_table
from errors_module.errors import APIBadRequest
from loguru import logger
from database_calls.facebook.calls import filter_images
import json
import base64
from io import BytesIO
from PIL import Image

FACEBOOK_BP = Blueprint("facebook", url_prefix="/facebook")





# @FACEBOOK_BP.route('/serve')
# async def serve(request):
#     path = request.args.get("path")

#     request.app.url_for(path) 

# FACEBOOK_BP.static('/profile',  "~/.datapod/userdata/raw/facebook/photos_and_videos/Profilepictures_IHIxz3DIcQ/")


# @FACEBOOK_BP.post('/parse')
# async def parse(request):




@FACEBOOK_BP.post('/parse')
async def parse(request):
    """
    To get all the assets created by the requester
    """
    import zipfile
    request.app.config.VALIDATE_FIELDS(["path"], request.json)




    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    try:
        the_zip_file = zipfile.ZipFile(request.json["path"])
    except:
        raise APIBadRequest("Invalid zip takeout file")


    logger.info(f"Testing zip {request.json['path']} file")
    ret = the_zip_file.testzip()

    if ret is not None:
        raise APIBadRequest("Invalid zip takeout file")

    ##check if mbox file exists or not



    logger.info("Copying and extracting facebook data")

    ds_path = os.path.join(request.app.config.RAW_DATA_PATH, "facebook")
    try:
        shutil.unpack_archive(request.json["path"], extract_dir=ds_path, format=None)
    except:
        raise APIBadRequest("Invalid zip facebook file")

    logger.info("Copying and extracting facebook data completed")




    request.app.add_task(__parse(request.app.config, ds_path))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Facebook data parsing has been Started and you will be notified once it is complete", 
        "data": None
        })



def image_base64(path):
    image = Image.open(path)
    buffered = BytesIO()
    image.save(buffered, format=image.format)
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode()

@FACEBOOK_BP.get('/images')
async def images(request):
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 20][request.args.get("number") == None] 
    result = await filter_images(request.app.config.FB_IMAGES_TBL , page, number)
    for image_data in result:
        path = image_data['uri']
        encoded_string = "data:image/jpeg;base64," + image_base64(path)
            
        if image_data.get("comments"):
            comments = json.loads(image_data.get("comments"))
            image_data.update({"comments": comments, "path": path, "uri": encoded_string})
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": None, 
        "data": result
        })

@FACEBOOK_BP.post('/chats')
async def allchats(request):
    """
    To get all the chats created by the user
    """
    request.app.config.VALIDATE_FIELDS(["message_type"], request.json)
    ds_path = os.path.join(request.app.config.RAW_DATA_PATH, "facebook/messages")
    chat_types = os.listdir(ds_path)

    if request.json.get("message_type") not in chat_types:
        raise APIBadRequest("This message type is not available")


    chat_path = os.path.join(ds_path, request.json.get("message_type"))

    all_chats = os.listdir(chat_path)
    result = [{"name": e.split("_")[0], "chat_id": e} for e in all_chats]

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Facebook data parsing has been Started and you will be notified once it is complete", 
        "data": result
        })

@FACEBOOK_BP.get('/chat')
async def single_chat(request):
    """
    To get all the chats created by the user
    """

    chat_id = request.args.get("chat_id")
    message_type = request.args.get("message_type")
    if not chat_id:
        raise APIBadRequest("chat id  is required")
    
    if not message_type:
        raise APIBadRequest("message_type is required")
    

    logger.info(f'This is the chat id {request.args.get("chat_id")}')
    ds_path = os.path.join(request.app.config.RAW_DATA_PATH, f"facebook/messages/{message_type}/{chat_id}")

    if not os.path.exists(ds_path):
        raise APIBadRequest("This chat doesnt exists")

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
