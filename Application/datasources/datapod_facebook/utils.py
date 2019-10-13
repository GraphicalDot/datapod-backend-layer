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
from .db_calls import store_image, update_datasources_status, update_stats

parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

sys.path.append(parent_module_path)

#from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, delete_key
import aiomisc



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

    await update_stats_table(config, datasource_name, username, "manual")
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

@aiomisc.threaded_separate
def get_dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')


@aiomisc.threaded_separate
def calc_data_items(dirpath):
    return len([os.path.join(basedir, filename) for basedir, dirs, files in os.walk(dirpath) for filename in files])



async def update_stats_table(config, datasource_name, username, sync_type):
    path = os.path.join(config.RAW_DATA_PATH, f"{DATASOURCE_NAME}/{username}")

    size = await get_dir_size(path)

    data_items = await calc_data_items(path)

    logger.info(f"Total size for {datasource_name} is {size}") 
    logger.info(f"Total data items for {datasource_name} is {data_items}") 
    u = datetime.datetime.utcnow()
    f  = datetime.timedelta(days=7)
    next_sync = u +f
    await update_stats(config[datasource_name]["tables"]["stats"], DATASOURCE_NAME, username, 
            data_items, size, config.DEFAULT_SYNC_FREQUENCY, sync_type, next_sync)

    return 

