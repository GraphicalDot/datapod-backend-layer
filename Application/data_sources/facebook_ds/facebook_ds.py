#-*- coding:utf-8 -*- 

import json
import os
import zipfile
import datetime
import pytz
import sys
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

sys.path.append(parent_module_path)

from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, delete_key


def indian_time_stamp(naive_timestamp=None):
    tz_kolkata = pytz.timezone('Asia/Kolkata')
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp.strftime(time_format + " %Z%z")





async def data_parse(app, path):
    ##add this if this has to executed periodically
    ##while True:
    async def change_uri(json_data, prefix_path):
        for entry in json_data["photos"]:
            uri = os.path.join(prefix_path, entry["uri"])
            timestamp = indian_time_stamp(entry["creation_timestamp"])
            entry.update({"uri": uri, "creation_timestamp": timestamp})
        return json_data["photos"]

    #path = "/home/feynman/Programs/datapod-backend-layer/Application/userdata/facebook/"
    facebook_images = f"{path}/photos_and_videos/album/"

    json_files= [(os.path.join(facebook_images, file)) for file in os.listdir(facebook_images)]

    images = []

    for _file in json_files:
        with open(_file, "r") as json_file:   
            data = json.load(json_file)
            images.extend(await change_uri(data, path))

    logger.info(images)


    db_instance = create_db_instance(app.config.db_dir_path)
    stored_value = get_key("logs", db_instance)

    value = [{"date": indian_time_stamp(), 
            "status": "success", 
            "message": "Facebook data has been parsed successfully"}]
    
    if stored_value:
        value = value+stored_value  

    #logger.info(f"value stored against logs is {value}")
    insert_key("logs", value, db_instance)

    insert_key("facebook_images", images, db_instance)


    stored_value = get_key("services", db_instance)
    logger.info("Stored value against services %s"%stored_value)

    #delete_key("services", db_instance)
    value = [{"time": indian_time_stamp(), 
            "service": "facebook", 
            "message": f"{len(images)} images present"}]
    
    if stored_value:
        
        for entry in stored_value:
            if entry.get("service") == "facebook":
                break
        stored_value.remove(entry)
        stored_value.extend(value)
    else:
        stored_value = value

    insert_key("services", stored_value, db_instance)

    close_db_instance(db_instance)

    return 