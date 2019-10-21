#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import aiomisc
#@retry(stop=stop_after_attempt(2))


@aiomisc.threaded
def update_datasources_status(facebook_status_table, datasource_name, username, status):
    try:
        facebook_status_table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        facebook_status_table.update(
            status=status).\
        where(facebook_status_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 


@aiomisc.threaded
def update_stats(facebook_stats_table, datasource_name, username, data_items, size, sync_frequency, sync_type, next_sync):
    """

    """
    try:
        facebook_stats_table.insert(
                source = datasource_name,
                username = username,
                data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).execute()
                                    
    except IntegrityError as e:
        logger.error(f"Couldnt insert stats for  {datasource_name} because of {e} so updating it")

        facebook_stats_table.update(
                            data_items = data_items,
                disk_space_used = size).\
        where(facebook_stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 




@aiomisc.threaded
def get_status(facebook_status_table):
    return facebook_status_table.select().dicts()
                                    


@aiomisc.threaded
def get_stats(facebook_stats_table):
    return facebook_stats_table.select().dicts()
        


@aiomisc.threaded
def store_creds(tbl_object, username, password):
    """
    purchases: a list of purchases dict
    """


    try:
        tbl_object.insert(
                    username = username,
                    password=password).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
   
    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Github creds data insertion failed {username} with {e}")
    return 


@aiomisc.threaded
def store_image(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]
    if data.get("comments"):
        comments = json.dumps(data["comments"])
    else:
        comments = None

    if data.get("media_metadata"):
        media_metadata =  json.dumps(data["media_metadata"])
    else:
        media_metadata = None


    try:
        table.insert(
                    title = data["title"],
                    comments = comments,
                    media_metadata = media_metadata,
                    uri = data["uri"],
                    creation_timestamp = data.get("creation_timestamp"),
                    username = data.get("username"),
                    checksum=data.get("checksum")
                    ).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f'Duplicate key present --{data.get("uri")}-- in table --FBdata-- {e}')
        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"facebook image data insertion failed {data.get('uri')} with {e}")
    return 


@aiomisc.threaded
def filter_images(tbl_object, start_date, end_date, skip, limit, username):
    logger.error(f"Name of the tanble is {tbl_object} --- {username}")

    if start_date and end_date:

        query = tbl_object\
                .select()\
                .where((tbl_object.creation_timestamp> start_date) &(tbl_object.creation_timestamp < end_date) & (tbl_object.username==username))\
                .order_by(-tbl_object.creation_timestamp)
                
        

    elif start_date and not end_date:
        query = tbl_object\
                        .select()\
                        .where((tbl_object.creation_timestamp> start_date)& (tbl_object.username==username))\
                        .order_by(-tbl_object.creation_timestamp)
                        


    elif end_date and not start_date:
        query = tbl_object\
                        .select()\
                        .where((tbl_object.creation_timestamp < end_date)&((tbl_object.username==username)))\
                        .order_by(-tbl_object.creation_timestamp)
        


    else: # not  start_date and  not end_date

        query = tbl_object\
                .select()\
                .where(tbl_object.username==username)\
                .order_by(-tbl_object.creation_timestamp)

    
    return query.offset(skip).limit(limit).dicts(), query.count()
    