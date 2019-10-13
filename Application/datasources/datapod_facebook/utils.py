#-*- coding:utf-8 -*- 

import json
import os
import zipfile
import datetime
import pytz
import sys
from errors_module.errors import APIBadRequest
from loguru import logger

from .db_calls import store_image, update_datasources_status

parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

sys.path.append(parent_module_path)

#from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, delete_key



async def __parse(config, path, username, checksum, datasource_name):
    ##add this if this has to executed periodically
    ##while True:
    #path = /home/feynman/.datapod/userdata/raw/facebook/
    await update_datasources_status(config[datasource_name]["tables"]["status"], datasource_name, username, "PROGRESS")
    
    async def change_uri(json_data, prefix_path):
        i = 100/len(json_data["photos"])
        for  num, entry in enumerate(json_data["photos"]):
            uri = os.path.join(prefix_path, entry["uri"])
            #timestamp = indian_time_stamp(entry["creation_timestamp"])
            timestamp = datetime.datetime.utcfromtimestamp(entry["creation_timestamp"])
            entry.update({"uri": uri, "creation_timestamp": timestamp, 
                "tbl_object": config[datasource_name]["tables"]["image_table"], 
                "username": username, "checksum": checksum})
            
            logger.info(entry)
            res = {"message": "Progress", "percentage": int(i*(num+1))}

            await store_image(**entry)
            await config["send_sse_message"](config, datasource_name, res)

        return json_data["photos"]

    #path = "/home/feynman/Programs/datapod-backend-layer/Application/userdata/facebook/"
    facebook_images = f"{path}/photos_and_videos/album/"

    json_files= [(os.path.join(facebook_images, file)) for file in os.listdir(facebook_images)]

    images = []

    for _file in json_files:
        with open(_file, "r") as json_file:   
            data = json.load(json_file)
            images.extend(await change_uri(data, path))


    await update_datasources_status(config[datasource_name]["tables"]["status"], datasource_name, username, "COMPLETED")

    res = {"message": "completed", "percentage": 100}
    await config["send_sse_message"](config, datasource_name, res)

    return 


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
