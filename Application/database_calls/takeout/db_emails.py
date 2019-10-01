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
                        message_type= data["message_type"],
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



@async_wrap
def get_email_attachment(tbl_object, message_type, start_date, end_date, skip, limit):
    """
    purchases: a list of purchases dict
    """
    # email_attachment_table = tbl_object
    # return email_attachment_table\
    #             .select()\
    #             .order_by(-email_attachment_table.date)\
    #             .paginate(page, number)\
    #             .dicts()

    if start_date and end_date:
        logger.info("Start date and  end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date) &(tbl_object.date < end_date))
                
        

    elif start_date and not end_date:
                        
        logger.info("Start date and but not end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date))
                

    elif end_date and not start_date:
        logger.info("not Start date and but end date")
        
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date < end_date))
                


    else: # not  start_date and  not end_date
        logger.info("Start date and end date is not present")
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where(tbl_object.message_type== message_type)
                

    return  query.offset(skip).limit(limit).dicts(), query.count()



@async_wrap
def get_emails(tbl_object, message_type, start_date, end_date, skip, limit):
    """
    purchases: a list of purchases dict
    """


    # return email_attachment_table\
    #             .select()\
    #             .order_by(-email_attachment_table.date)\
    #             .where(email_attachment_table.message_type== message_type)\
    #             .paginate(page, number)\
    #             .dicts()



    if start_date and end_date:
        logger.info("Start date and  end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date) &(tbl_object.date < end_date))
                
        

    elif start_date and not end_date:
                        
        logger.info("Start date and but not end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date))
                

    elif end_date and not start_date:
        logger.info("not Start date and but end date")
        
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date < end_date))
                


    else: # not  start_date and  not end_date
        logger.info("Start date and end date is not present")
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where(tbl_object.message_type== message_type)
                

    return  query.offset(skip).limit(limit).dicts(), query.count()

@async_wrap
def match_text(tbl_object, indexed_obj, matching_string, message_type, start_date, end_date, skip, limit):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    # query = (tbl_object
    #             .select()
    #             .join(index_email_obj, on=(email_tbl_object.email_id == index_email_obj.email_id))
    #             .where(index_email_obj.match(matching_string))
    #             .dicts())
    # return list(query)

    

    if start_date and end_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id))\
                .where(indexed_obj.match(matching_string) & (tbl_object.date> start_date) &(tbl_object.date < end_date) &(tbl_object.message_type== message_type))\
                .order_by(-tbl_object.date)

                
        

    elif start_date and not end_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id))\
                .where((indexed_obj.match(matching_string)) & (tbl_object.date> start_date) &(tbl_object.message_type== message_type))\
                .order_by(-tbl_object.date)

        


    elif end_date and not start_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id))\
                .where((indexed_obj.match(matching_string)) &(tbl_object.date < end_date) & (tbl_object.message_type== message_type))\
                .order_by(-tbl_object.date)



    else: # not  start_date and  not end_date
        query = tbl_object\
                    .select()\
                    .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id) &(tbl_object.message_type== message_type))\
                    .where(indexed_obj.match(matching_string))\


    return  query.offset(skip).limit(limit).dicts(), query.count()
