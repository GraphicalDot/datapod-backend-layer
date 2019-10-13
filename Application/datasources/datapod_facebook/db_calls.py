#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from tenacity import *
from loguru import logger
from utils.utils import async_wrap

#@retry(stop=stop_after_attempt(2))


@async_wrap
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


@async_wrap
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


@async_wrap #makes function asynchronous
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


@async_wrap
def get_single_repository(tbl_object, name):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (tbl_object\
            .select()\
            .where(tbl_object.name==name).dicts())
    return list(query)





@async_wrap
def counts(tbl_object):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    gists = tbl_object\
            .select()\
            .where(tbl_object.is_gist==True).count()
    
    repos = tbl_object\
            .select()\
            .where(tbl_object.is_gist != True, tbl_object.is_starred != True).count()

    starred = tbl_object\
            .select()\
            .where(tbl_object.is_starred==True).count()



    return {
        "gists_count": gists,
        "starred_count": starred,
        "repos_count": repos,
    }
