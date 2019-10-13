#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from tenacity import *
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
def filter_images(tbl_object, page, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select()\
            .order_by(-tbl_object.creation_timestamp)\
            .paginate(page, number)\
             .dicts()
