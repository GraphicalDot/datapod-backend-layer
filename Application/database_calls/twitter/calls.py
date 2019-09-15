#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from tenacity import *
from loguru import logger
from utils.utils import async_wrap
import hashlib
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

@async_wrap #makes function asynchronous
def get_creds(tbl_object):
        res = tbl_object.get_by_id(1)
        return res.username, res.password

@async_wrap
def store(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    logger.info(table)
    if data.get("entities"):
        entities=  json.dumps(data.get("entities"))
    else:
        entities = None



    if data.get("symbols"):
        symbols=  json.dumps(data.get("symbols"))
    else:
        symbols = None

    if data.get("display_text_range"):
        display_text_range=  json.dumps(data.get("display_text_range"))
    else:
        display_text_range = None

    tweet_hash = hashlib.sha256(data["full_text"].encode()).hexdigest()
    logger.info(f"Tweet hash is {tweet_hash}")


    try:
        table.insert(
                    tweet_hash = tweet_hash,
                    retweeted = data.get("retweeted"),
                    source = data.get("source"),
                    entities =entities,
                    symbols =symbols,
                    display_text_range=display_text_range,
                    favorite_count= data.get("favorite_count"),
                    id_str=data.get("id_str"),
                    possibly_sensitive = data.get("possibly_sensitive"),
                    truncated=data.get("truncated"),
                    retweet_count=data.get("retweet_count"),
                    created_at=data.get("created_at"),
                    favorited=data.get("favorited"),
                    full_text=data.get("full_text"),
                    lang=data.get("lang"),
                    in_reply_to_screen_name=data.get("in_reply_to_screen_name"),
                    in_reply_to_user_id_str=data.get("in_reply_to_user_id_str")).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet data insertion failed {data.get('id_str')} with Duplicate Key")
        pass

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet data insertion failed {data.get('id_str')} with {e}")
    return 




@async_wrap #makes function asynchronous
def filter_gists(tbl_object, page, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select(tbl_object.name, tbl_object.git_pull_url, 
                    tbl_object.downloaded_at, 
                    tbl_object.id, 
                    tbl_object.node_id, 
                    tbl_object.created_at, 
                    tbl_object.updated_at, 
                    tbl_object.pushed_at,
                    tbl_object.description)\
            .where(tbl_object.is_gist==True)\
            .order_by(-tbl_object.updated_at)\
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
