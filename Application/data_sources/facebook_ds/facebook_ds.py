#-*- coding:utf-8 -*- 

import json
import os
import zipfile
import datetime
import pytz
import sys
from errors_module.errors import APIBadRequest
from loguru import logger

from database_calls.credentials import update_datasources_status
from database_calls.facebook.calls import store_image

parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

sys.path.append(parent_module_path)

#from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, delete_key


def indian_time_stamp(naive_timestamp=None):
    tz_kolkata = pytz.timezone('Asia/Kolkata')
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp.strftime(time_format + " %Z%z")





async def __parse(config, path):
    ##add this if this has to executed periodically
    ##while True:
    #path = /home/feynman/.datapod/userdata/raw/facebook/
    update_datasource_table(config, "PROGRESS")
    
    async def change_uri(json_data, prefix_path):
        for entry in json_data["photos"]:
            uri = os.path.join(prefix_path, entry["uri"])
            #timestamp = indian_time_stamp(entry["creation_timestamp"])
            timestamp = datetime.datetime.fromtimestamp(entry["creation_timestamp"])
            entry.update({"uri": uri, "creation_timestamp": timestamp, "tbl_object": config.FB_IMAGES_TBL})
            logger.info(entry)
            await store_image(**entry)

        return json_data["photos"]

    #path = "/home/feynman/Programs/datapod-backend-layer/Application/userdata/facebook/"
    facebook_images = f"{path}/photos_and_videos/album/"

    json_files= [(os.path.join(facebook_images, file)) for file in os.listdir(facebook_images)]

    images = []

    for _file in json_files:
        with open(_file, "r") as json_file:   
            data = json.load(json_file)
            images.extend(await change_uri(data, path))


    update_datasource_table(config, "COMPLETED")
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


def update_datasource_table(config, status):
    """
    Update data sources table after successful parsing of takeout and emails 
    """
    if status not in ["PROGRESS", "COMPLETED"]:
        raise APIBadRequest("Invalid status")

    data = {"tbl_object": config.DATASOURCES_TBL,
            "name": profile(config), 
            "source": "FACEBOOK", "message": "fb data parsing started",
            "code": config.DATASOURCES_CODE["FACEBOOK"],
            "status": status }

    update_datasources_status(**data)
    return 