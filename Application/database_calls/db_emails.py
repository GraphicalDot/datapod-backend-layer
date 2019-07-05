#-*- coding: utf-8 -*-

import json
import datetime
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)



def store_email(**data):
    """
    purchases: a list of purchases dict
    """
    email_table = data["tbl_object"]
    try:
        email_table.insert(email_id=data["email_id"], from_addr=data["from_addr"], 
                        to_addr=data["to_addr"], 
                        subject=data["subject"],
                        content=data["content"],
                        email_id_raw= data["email_id_raw"],
                        message_type = data["message_type"],
                        attachments = data["attachments"],
                       date=data["date"], path=data["path"]).execute()

        logger.success(f"Success on insert email_id --{data['email_id']}-- email_id_raw --{data['email_id_raw']}-- \
                                    and path --{data['path']}--")
    except Exception as e:
        logger.error(f"Error on insert email_id --{data['email_id']}-- email_id_raw --{data['email_id_raw']}-- \
            and path --{data['path']}-- with error {e}")
    return 



def store_email_content(**data):
    """
    purchases: a list of purchases dict
    """
    index_email_content_table = data["tbl_object"]

    try:
        index_email_content_table.insert(email_id=data["email_id"], 
                        content=data["content"]).execute()

        logger.success(f"Success on insert indexed content for  email_id --{data['email_id']}-- ")
    except Exception as e:
        logger.error(f"Error on insert indexed content for  email_id --{data['email_id']}-- with error {e}")
    return 



def store_email_attachment(**data):
    """
    purchases: a list of purchases dict
    """
    email_attachment_table = data["tbl_object"]
    try:
        email_attachment_table.insert(email_id=data["email_id"], 
                        path=data["path"], 
                        attachment_name=data["attachment_name"], 
                       date=data["date"]).execute()

        logger.success(f"Success on insert attachement for  email_id --{data['email_id']}--  \
                                    path --{data['path']}-- and attachement name {data['attachment_name']}")
    except Exception as e:
        logger.error(f"Error on insert attachement for  email_id --{data['email_id']}--  \
                                    path --{data['path']}-- and attachement name {data['attachment_name']}\
                                    with error {e}")

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


