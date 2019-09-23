#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from tenacity import *
from loguru import logger
from utils.utils import async_wrap
import hashlib
from dateutil.parser import parse
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
def store(**tweet):
    """
    purchases: a list of purchases dict
    """
    table = tweet["tbl_object"]

    if tweet.get("entities"):
        entities=  json.dumps(tweet.get("entities"))
    else:
        entities = None



    if tweet.get("symbols"):
        symbols=  json.dumps(tweet.get("symbols"))
    else:
        symbols = None

    if tweet.get("display_text_range"):
        display_text_range=  json.dumps(tweet.get("display_text_range"))
    else:
        display_text_range = None

    tweet_hash = hashlib.sha256(tweet["full_text"].encode()).hexdigest()
    logger.info(f"Tweet hash is {tweet_hash}")


    ##this will extract all the hashtags from the tweet, if the present and creates 
    ## a string with all the hashtags in it
    hashtags = ""  
    
    if tweet.get('entities'): 
        if tweet['entities'].get("hashtags"): 
            for tag in tweet['entities'].get("hashtags"): 
                hashtags= hashtags + ", " + tag.get('text') 
    logger.info(f"hashtags == {hashtags}") 

    ##this will extract all the user mentions from the tweet, if the present and creates 
    ## a string with all the hashtags in it

    user_mentions=""
    if tweet.get('entities'): 
        if tweet['entities'].get("user_mentions"): 
            for tag in tweet['entities'].get("user_mentions"): 
                user_mentions= user_mentions + ", " + tag.get('name')+ ", " +tag.get('screen_name') 
    logger.info(f"user_mentions == {user_mentions}") 


    ##this is the content wchihc will be indexed under FTS5 model
    content_to_be_indexed = tweet.get("full_text") + " " + hashtags + " " + user_mentions
    logger.info(f"Content which will be indexed is {content_to_be_indexed}")

    indexed_table = tweet["indexed_tbl_object"]


    try:
        table.insert(
                    tweet_hash = tweet_hash,
                    retweeted = tweet.get("retweeted"),
                    source = tweet.get("source"),
                    entities =entities,
                    symbols =symbols,
                    display_text_range=display_text_range,
                    favorite_count= tweet.get("favorite_count"),
                    id_str=tweet.get("id_str"),
                    possibly_sensitive = tweet.get("possibly_sensitive"),
                    truncated=tweet.get("truncated"),
                    retweet_count=tweet.get("retweet_count"),
                    created_at=parse(tweet.get("created_at")),
                    favorited=tweet.get("favorited"),
                    full_text=tweet.get("full_text"),
                    lang=tweet.get("lang"),
                    in_reply_to_screen_name=tweet.get("in_reply_to_screen_name"),
                    in_reply_to_user_id_str=tweet.get("in_reply_to_user_id_str")).execute()

        indexed_table.insert(tweet_hash = tweet_hash,
                            content=content_to_be_indexed).execute()

        #logger.success(f"Success on insert email_id --{tweet['email_id']}-- path --{tweet['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet tweet insertion failed {tweet.get('id_str')} with Duplicate Key")
        pass

    except Exception as e:
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet tweet insertion failed {tweet.get('id_str')} with {e}")
    return 


@async_wrap
def store_account(**account_data):
    table = account_data["tbl_object"]

    try:
        table.insert(
                    phone_number=account_data.get("phoneNumber"),
                    email=account_data.get("email"),
                    created_at = account_data.get("createdAt"),
                    username = account_data.get("username"),
                    account_id = account_data.get("accountId"),
                    created_via= account_data.get("createdVia"),
                    account_display_name = account_data.get("accountDisplayName")).execute()

        #logger.success(f"Success on insert email_id --{tweet['email_id']}-- path --{tweet['path']}--")
    except IntegrityError as e:
        table.update(
                    phone_number=account_data.get("phoneNumber"),
                    email=account_data.get("email"),
                    created_at = account_data.get("createdAt"),
                    username = account_data.get("username"),
                    account_id = account_data.get("accountId"),
                    created_via= account_data.get("createdVia"),
                    account_display_name = account_data.get("accountDisplayName")).\
                        where(table.account_id==account_data.get("accountId"))\
                        .execute()
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Twitter Account Data insertion failed {account_data.get('accountDisplayName')} with Duplicate Key but update assucessful")
        pass

    except Exception as e:
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet tweet insertion failed {account_data.get('accountDisplayName')} with {e}")
    return 
    




@async_wrap #makes function asynchronous
def filter_tweet(tbl_object, skip, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select()\
            .order_by(-tbl_object.created_at)\
            .offset(skip)\
            .limit(number)\
             .dicts()


@async_wrap #makes function asynchronous
def count_tweets(tbl_object):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select()\
            .count()


@async_wrap #makes function asynchronous
def match_text(main_tbl_object, indexed_obj, matching_string, page, number,  time=None):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (main_tbl_object
                .select()
                .join(indexed_obj, on=(main_tbl_object.tweet_hash == indexed_obj.tweet_hash))
                .where(indexed_obj.match(matching_string))
                .dicts())
    return list(query)

@async_wrap #makes function asynchronous
def count_filtered_tweets(main_tbl_object, indexed_obj, matching_string, time=None):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    count = main_tbl_object\
                .select()\
                .join(indexed_obj, on=(main_tbl_object.tweet_hash == indexed_obj.tweet_hash))\
                .where(indexed_obj.match(matching_string))\
                .count()
    return count
