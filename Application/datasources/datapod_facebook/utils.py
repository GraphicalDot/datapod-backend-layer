#-*- coding:utf-8 -*- 

import json
import os
import zipfile
import datetime
import pytz
import sys
import subprocess
from errors_module.errors import APIBadRequest
from loguru import logger
from .variables import DATASOURCE_NAME
import humanize
from .db_calls import store_image, update_status, update_stats, store_chats

parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

sys.path.append(parent_module_path)

import aiomisc



async def __parse(config, path, username, checksum):
    ##add this if this has to executed periodically
    ##while True:
    #path = /home/feynman/.datapod/userdata/raw/facebook/
    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "PROGRESS")
    
    async def change_uri(json_data, prefix_path):
        i = 95/len(json_data["photos"])
        for  num, entry in enumerate(json_data["photos"]):
            
            
            _, file_extension = os.path.splitext(entry["uri"])

            uri = os.path.join(prefix_path, entry["uri"])
            #timestamp = indian_time_stamp(entry["creation_timestamp"])
            timestamp = datetime.datetime.utcfromtimestamp(entry["creation_timestamp"])
            
            
            entry.update({"uri": uri, "creation_timestamp": timestamp, 
                "tbl_object": config[DATASOURCE_NAME]["tables"]["image_table"], 
                "username": username, 
                "chat_image": False,
                "file_extension": file_extension,
                "checksum": checksum})
            
            res = {"message": "Progress", "percentage": int(i*(num+1))}

            await store_image(**entry)
            await config["send_sse_message"](config, DATASOURCE_NAME, res)

        return json_data["photos"]

    #path = "/home/feynman/Programs/datapod-backend-layer/Application/userdata/facebook/"
    #facebook_images = f"{path}/photos_and_videos/album/"
    
    facebook_images = os.path.join(path, "photos_and_videos", "album")
    facebook_chats_path = os.path.join(path, "messages")


    json_files= [(os.path.join(facebook_images, file)) for file in os.listdir(facebook_images)]

    images = []

    for _file in json_files:
        with open(_file, "r") as json_file:   
            data = json.load(json_file)
            images.extend(await change_uri(data, path))


    ##handle chats
    await handle_chats(config, username, checksum, facebook_chats_path)

    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "COMPLETED")

    res = {"message": "completed", "percentage": 100}
    await config["send_sse_message"](config, DATASOURCE_NAME, res)



    takeout_dir = os.path.join(config["RAW_DATA_PATH"], DATASOURCE_NAME, username)


    # usernames = [{"username": x[0], "path": os.path.join(datasource_dir, x[0])} for x in os.walk(datasource_dir)]
    size = dir_size(takeout_dir)
    data_items = files_count(takeout_dir) 
    logger.success(f"username == {takeout_dir} size == {size} dataitems == {data_items}")

    await update_stats(config[DATASOURCE_NAME]["tables"]["stats_table"], 
                DATASOURCE_NAME, 
                username, data_items, size, "weekly", "auto", datetime.datetime.utcnow() + datetime.timedelta(days=7) ) 


    return 





async def handle_chats(config, username, checksum, chats_path):
    """
    To get all the chats created by the user
    """
    #request.app.config.VALIDATE_FIELDS(["message_type"], request.json)
    #ds_path = os.path.join(request.app.config.RAW_DATA_PATH, "facebook/messages")
    chat_types = os.listdir(chats_path)

    for chat_type in ["stickers_used"]:
        if chat_type in chat_types:
            chat_types.remove(chat_type)

    for chat_type in chat_types:
        ##this will be names type like archieved, inbox etc
        chat_type_path = os.path.join(chats_path, chat_type)

        all_chats = os.listdir(chat_type_path)
        #chat_ids = [{"name": e.split("_")[0], "chat_id": e} for e in all_chats]


        #in every type, there will be several chat folders correponding to the chats 
        # with the users 
        for chat_id in all_chats:
            #actual chat path with the name of the chat folder, abolsute path in which 
            # the chat is stored in json format  
            chat_path = os.path.join(chat_type_path, chat_id)
            await read_chat(config, username, checksum, chat_path, chat_type, chat_id)
            

    return 






async def read_chat(config, username, checksum, chat_path, chat_type, chat_id):
    
    #ds_path = os.path.join(config.RAW_DATA_PATH, f"facebook/messages/{chat_type}/{chat_id}")

    result = {}

    chat_files= [os.path.join(chat_path, file) for file in os.listdir(chat_path) if os.path.isfile(os.path.join(chat_path, file))]
    phots_directories= [os.path.join(chat_path, file) for file in os.listdir(chat_path) if os.path.isdir(os.path.join(chat_path, file))]
    logger.info(chat_files)


    if len(chat_files) != 0:
        for chat_file in chat_files:
            ##multiple files for the different chats with the user may be present
            ##it has been decided that we should store all these ifferent chats with same user as different 
            ##objects in the database, Ou unique identifier will be chat_file also
            with open(chat_file, "r") as json_file:
                data = json.load(json_file)


                participants = json.dumps(chat_participants(data.get("participants")))
                messages = json.dumps(data.get("messages"))
                message_content = _message_content(data.get("messages"))
                title = data.get("title")
                thread_type = data.get("thread_type").lower()
                #extracting only one message out of all the messages

                ##extracting the timestamp of the last message
                if data.get("messages"):
                    timestamp_ms = data.get("messages")[0]["timestamp_ms"]
                else:
                    timestamp_ms = None
        

                result.update({"chat_table":  config[DATASOURCE_NAME]["tables"]["chat_table"],
                                "username": username, 
                                "checksum": checksum, 
                                "title": title, 
                                "chat_type": chat_type,
                                "chat_id": chat_id,
                                "chat_path": chat_file,
                                "participants": participants, 
                                "thread_type": thread_type, 
                                "messages": messages, 
                                "message_content": message_content.lower(),
                                "timestamp": timestamp_ms })
                await store_chats(**result)


    ##these will be phots directories (absolute path) like photos, gifs etc
    if phots_directories:
        for photodir in phots_directories:
            await chat_photos(config, photodir, username, checksum, chat_id) 
    logger.info(f"Phots directories {phots_directories}")

    # else:
    #     chat_photo_folder = os.path.join(chat_path)
    #     await chat_photos(chat_type, chat_id, chat_photo_folder)

    

    return     



def chat_participants(participants_dict):
    """
        "participants": [
            {
            "name": "Akanksha Priyadarshini"
            },
            {
            "name": "Saurav Verma"
            }
    """
    return [e.get("name") for e in participants_dict]


def _message_content(message_list):
    """
    """
    if message_list:
        return " ".join([e.get("content") for e in message_list if e.get("content")])
    return None


async def chat_photos(config, chat_photo_folder, username, checksum, chat_id):
    """
    A chat can have a photos folder where the user has exchanged photos, read them and place them 
    in the photos
    """
    entry = {}
    onlyfiles = [f for f in os.listdir(chat_photo_folder) if os.path.isfile(os.path.join(chat_photo_folder, f))]
    for image in onlyfiles:
        image_path = os.path.join(chat_photo_folder, image)
        uri = image_path
        #timestamp = indian_time_stamp(entry["creation_timestamp"])
        timestamp = datetime.datetime.utcnow()
        _, file_extension = os.path.splitext(image)
        logger.info(entry)
        entry.update({"uri": uri, "creation_timestamp": timestamp, 
            "tbl_object": config[DATASOURCE_NAME]["tables"]["image_table"], 
            "username": username, 
            "checksum": checksum,
            "chat_image": True,
            "creation_timestamp": timestamp,
            "file_extension": file_extension,
            "title": chat_id,
            })
        
        await store_image(**entry)
           
    return






def dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')



def files_count(dirpath):
    return sum([len(files) for r, d, files in os.walk(dirpath)])





def profile(config):

    profile = os.path.join(config.RAW_DATA_PATH, "facebook/profile_information/profile_information.json") 
    if os.path.exists(profile):
        with open(profile, "r") as json_file:   
            data = json.load(json_file)

    try:
        name = data["profile"]["name"]["full_name"]
    except :
        name = "Dummy facebook name"

    return name

@aiomisc.threaded_separate
def get_dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')


@aiomisc.threaded_separate
def calc_data_items(dirpath):
    return len([os.path.join(basedir, filename) for basedir, dirs, files in os.walk(dirpath) for filename in files])



# async def update_stats_table(config, datasource_name, username, sync_type):
#     path = os.path.join(config.RAW_DATA_PATH, f"{DATASOURCE_NAME}/{username}")

#     size = await get_dir_size(path)

#     data_items = await calc_data_items(path)

#     logger.info(f"Total size for {datasource_name} is {size}") 
#     logger.info(f"Total data items for {datasource_name} is {data_items}") 
#     u = datetime.datetime.utcnow()
#     f  = datetime.timedelta(days=7)
#     next_sync = u +f
#     await update_stats(config[datasource_name]["tables"]["stats"], DATASOURCE_NAME, username, 
#             data_items, size, config.DEFAULT_SYNC_FREQUENCY, sync_type, next_sync)

#     return 

