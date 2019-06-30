#-*- coding: utf-8 -*-

import json
import datetime
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

async def store(tbl_object, source, creation_time, modification_time,
            photo_taken_time, description, url, title, geo_data, image_path):
    """
    purchases: a list of purchases dict
    """
    try:
        geo_data = json.dumps(geo_data)
        tbl_object.insert(source=source, creation_time=creation_time, 
                        modification_time=modification_time, 
                        photo_taken_time=photo_taken_time,
                        description=description,
                        url=url, title=title, geo_data=geo_data, 
                        image_path=image_path).execute()

        logger.success(f"success on insert {source} image {image_path}")
    except Exception as e:
        logger.error(f"Error on insert image {source} imge {image_path}  because of {e}")
    return 

def filter_date(tbl_object, page, number,  time=None):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
  
    if time:
        if type(time) != datetime.datetime:
            raise APIBadRequest("Datetime format is wrong")
        return tbl_object\
                .select()\
                .where(tbl_object.creation_time == time)\
                .order_by(-tbl_object.time)\
                .paginate(page, number)\
                .dicts()
    else:
        return tbl_object\
                .select()\
                .order_by(-tbl_object.creation_time)\
                .paginate(page, number)\
                .dicts()


