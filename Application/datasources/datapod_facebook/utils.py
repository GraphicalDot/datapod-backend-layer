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
from .db_calls import store_image, update_status, update_stats

parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

sys.path.append(parent_module_path)

import aiomisc


def dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')



def files_count(dirpath):
    return sum([len(files) for r, d, files in os.walk(dirpath)])


async def __parse(config, path, username, checksum):
    ##add this if this has to executed periodically
    ##while True:
    #path = /home/feynman/.datapod/userdata/raw/facebook/
    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "PROGRESS")
    
    async def change_uri(json_data, prefix_path):
        i = 100/len(json_data["photos"])
        for  num, entry in enumerate(json_data["photos"]):
            uri = os.path.join(prefix_path, entry["uri"])
            #timestamp = indian_time_stamp(entry["creation_timestamp"])
            timestamp = datetime.datetime.utcfromtimestamp(entry["creation_timestamp"])
            entry.update({"uri": uri, "creation_timestamp": timestamp, 
                "tbl_object": config[DATASOURCE_NAME]["tables"]["image_table"], 
                "username": username, "checksum": checksum})
            
            logger.info(entry)
            res = {"message": "Progress", "percentage": int(i*(num+1))}

            await store_image(**entry)
            await config["send_sse_message"](config, DATASOURCE_NAME, res)

        return json_data["photos"]

    #path = "/home/feynman/Programs/datapod-backend-layer/Application/userdata/facebook/"
    facebook_images = f"{path}/photos_and_videos/album/"

    json_files= [(os.path.join(facebook_images, file)) for file in os.listdir(facebook_images)]

    images = []

    for _file in json_files:
        with open(_file, "r") as json_file:   
            data = json.load(json_file)
            images.extend(await change_uri(data, path))


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

