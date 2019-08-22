#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
#from tenacity import *
from loguru import logger
from utils.utils import async_wrap, send_sse_message


#@retry(stop=stop_after_attempt(2))
@async_wrap
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

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        raise DuplicateEntryError(data['email_id'], "Email")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email data insertion failed {data['email_id']} with {e}")
 
    return 

@async_wrap
def store_email_content(**data):
    """
    purchases: a list of purchases dict
    """
    index_email_content_table = data["tbl_object"]

    try:
        index_email_content_table.insert(email_id=data["email_id"], 
                        content=data["content"],
                        content_hash=data["content_hash"]).execute()

        #logger.success(f"Success on insert indexed content for  email_id --{data['email_id']}-- ")


    except IntegrityError as e:
        logger.error(f"Error on insert indexed content for  email_id --{data['email_id']}-- with error {e}")
    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email content insertion failed {data['email_id']} with {e}")
    return



#@retry(stop=stop_after_attempt(2))
@async_wrap
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

        # logger.success(f"Success on insert attachement for  email_id --{data['email_id']}--  \
        #                             path --{data['path']}-- and attachement name {data['attachment_name']}")

    except IntegrityError as e:
        logger.error(f"Error on insert attachement for  email_id --{data['email_id']}--  \
                                    path --{data['path']}-- and attachement name {data['attachment_name']}\
                                    with error {e}")
    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email sttachment insertion failed {data['email_id']} with {e}")
    return 


def match_text(email_tbl_object, index_email_obj, matching_string, page, number,  time=None):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (email_tbl_object
                .select()
                .join(index_email_obj, on=(email_tbl_object.email_id == index_email_obj.email_id))
                .where(index_email_obj.match(matching_string))
                .dicts())
    return list(query)

        # if time:
        #     if type(time) != datetime.datetime:
        #         raise APIBadRequest("Datetime format is wrong")
        #     return tbl_object\
        #             .select()\
        #             .where(tbl_object.creation_time == time)\
        #             .order_by(-tbl_object.time)\
        #             .paginate(page, number)\
        #             .dicts()
        # else:
        #     return tbl_object\
        #             .select()\
        #             .order_by(-tbl_object.creation_time)\
        #             .paginate(page, number)\
        #             .dicts()


