#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import hashlib
from dateutil.parser import parse
#@retry(stop=stop_after_attempt(2))
import aiomisc





@aiomisc.threaded
def update_status(status_table, datasource_name, username, status, path=None, original_path=None):
    try:
        status_table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    path = path,
                                    original_path=original_path
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        if path and original_path:
            status_table.update(
                status=status, 
                path = path,
                original_path=original_path).\
            where(status_table.username==username).\
            execute()
        elif original_path:
            status_table.update(
                            status=status, 
                            original_path=original_path).\
                        where(status_table.username==username).\
                        execute()

        elif path:
            status_table.update(
                            status=status, 
                            path=path).\
                        where(status_table.username==username).\
                        execute()
        else:
            status_table.update(
                            status=status).\
                        where(status_table.username==username).\
                        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 

@aiomisc.threaded
def delete_status(status_table, datasource_name, username):
    try:
        status_table.delete().where(status_table.username==username).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt delete {datasource_name} updated because of {e}")
    return 


@aiomisc.threaded
def update_stats(stats_table, datasource_name, username, data_items, size, sync_frequency, sync_type, next_sync):
    """

    """
    try:
        stats_table.insert(
                source = datasource_name,
                username = username,
                data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).execute()
                                    
    except IntegrityError as e:
        logger.error(f"Couldnt insert stats for  {datasource_name} because of {e} so updating it")

        stats_table.update(
                            data_items = data_items,
                disk_space_used = size).\
        where(stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 






@aiomisc.threaded
def get_status(status_table, username=None):
    logger.info(f"This is the username {username}")
    if not username:
        return status_table.select().dicts()
    return status_table.select().where(status_table.username==username).dicts()

@aiomisc.threaded
def get_stats(stats_table):
    return stats_table.select().dicts()

@aiomisc.threaded
def get_archives(table):
    return table.select().dicts()








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

@aiomisc.threaded #makes function asynchronous
def get_creds(tbl_object):
        res = tbl_object.get_by_id(1)
        return res.username, res.password

@aiomisc.threaded
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
    hashtag_list  = []  
    
    if tweet.get('entities'): 
        if tweet['entities'].get("hashtags"): 
            for tag in tweet['entities'].get("hashtags"): 
                hashtags= hashtags + ", " + tag.get('text') 
                hashtag_list.append(tag.get('text'))
    logger.info(f"hashtags == {hashtags}") 

    ##this will extract all the user mentions from the tweet, if the present and creates 
    ## a string with all the hashtags in it

    user_mentions=""
    user_mentions_list = []
    if tweet.get('entities'): 
        if tweet['entities'].get("user_mentions"): 
            for tag in tweet['entities'].get("user_mentions"): 
                user_mentions= user_mentions + ", " + tag.get('name')+ ", " +tag.get('screen_name') 
                user_mentions_list.append(tag.get('screen_name'))
    logger.info(f"user_mentions == {user_mentions}") 


    ##this is the content wchihc will be indexed under FTS5 model
    content_to_be_indexed = tweet.get("full_text") + " " + hashtags + " " + user_mentions
    logger.info(f"Content which will be indexed is {content_to_be_indexed}")

    indexed_table = tweet["indexed_tbl_object"]


    try:
        table.insert(
                    tweet_hash = tweet_hash,
                    username = tweet["username"],
                    checksum= tweet["checksum"],
                    retweeted = tweet.get("retweeted"),
                    source = tweet.get("source"),
                    entities =entities,
                    symbols =symbols,
                    display_text_range=display_text_range,
                    favorite_count= tweet.get("favorite_count"),
                    id_str=tweet.get("id_str"),
                    possibly_sensitive = tweet.get("possibly_sensitive"),
                    truncated=tweet.get("truncated"),
                    hashtags = hashtags,
                    user_mentions = user_mentions,
                    retweet_count=tweet.get("retweet_count"),
                    created_at=parse(tweet.get("created_at")),
                    favorited=tweet.get("favorited"),
                    full_text=tweet.get("full_text"),
                    lang=tweet.get("lang"),
                    in_reply_to_screen_name=tweet.get("in_reply_to_screen_name"),
                    in_reply_to_user_id_str=tweet.get("in_reply_to_user_id_str")).execute()

        indexed_table.insert(tweet_hash = tweet_hash, username=tweet["username"], checksum=tweet["checksum"],
                            content=content_to_be_indexed).execute()

        #logger.success(f"Success on insert email_id --{tweet['email_id']}-- path --{tweet['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet insertion failed {tweet.get('id_str')} with {e}")
        

    except Exception as e:
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Tweet tweet insertion failed {tweet.get('id_str')} with {e}")
    
    return hashtag_list, user_mentions_list


@aiomisc.threaded
def store_account(**account_data):
    table = account_data["tbl_object"]
    logger.info(account_data)
    try:
        table.insert(
                    username = account_data["username"],
                    checksum= account_data["checksum"],
                    phone_number=account_data.get("phoneNumber"),
                    email=account_data.get("email"),
                    follower_count=  account_data.get("follower_count"),
                    following_count=  account_data.get("following_count"),
                    list_created=  account_data.get("list_created"),
                    list_subscribed= account_data.get("list_subscribed"),
                    list_member=  account_data.get("list_member"),
                    likes=  account_data.get("likes"),
                    contacts=  account_data.get("contacts"),
                    tweets= account_data.get("tweets"),
                    created_at = account_data.get("createdAt"),
                    account_id = account_data.get("accountId"),
                    created_via= account_data.get("createdVia"),
                    common_hashtags = account_data.get("common_hashtags"), 
                    common_user_mentions = account_data.get("common_user_mentions"),

                    account_display_name = account_data.get("accountDisplayName")).execute()

        #logger.success(f"Success on insert email_id --{tweet['email_id']}-- path --{tweet['path']}--")
    except IntegrityError as e:
        table.update(

                    phone_number=account_data.get("phoneNumber"),
                    email=account_data.get("email"),
                    follower_count=  account_data.get("follower_count"),
                    following_count=  account_data.get("following_count"),
                    list_created=  account_data.get("list_created"),
                    list_subscribed= account_data.get("list_subscribed"),
                    list_member=  account_data.get("list_member"),
                    likes=  account_data.get("likes"),
                    contacts=  account_data.get("contacts"),
                    tweets= account_data.get("tweets"),
                    created_at = account_data.get("createdAt"),
                    username = account_data.get("username"),
                    account_id = account_data.get("accountId"),
                    common_hashtags = account_data.get("common_hashtags"), 
                    common_user_mentions = account_data.get("common_user_mentions"),
                    created_via= account_data.get("createdVia"),
                    account_display_name = account_data.get("accountDisplayName")).\
                        where(table.account_id==account_data.get("accountId"))\
                        .execute()
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Twitter Account Data insertion failed {account_data.get('accountDisplayName')} with Duplicate Key but update assucessful with {e}")

    except Exception as e:
        #raise DuplicateEntryError(tweet['email_id'], "Email")
        #use with tenacity
        logger.error(f"Twitter Account data insertion failed {account_data.get('accountDisplayName')} with {e}")
    return 
    

@aiomisc.threaded
def get_account(tbl_object, username):
    res =  tbl_object\
                .select()\
                .where(tbl_object.username == username)\
                .dicts()
    for e in res:
        logger.info(e)
    return res

@aiomisc.threaded #makes function asynchronous
def filter_tweet(tbl_object, username, start_date, end_date, skip, limit):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    ##startDate must be greater then Enddate


    if start_date and end_date:

        query = tbl_object\
                .select()\
                .where(tbl_object.username == username, 
                    tbl_object.created_at> start_date, 
                        tbl_object.created_at < end_date)\
                .order_by(-tbl_object.created_at)
                
        

    elif start_date and not end_date:
        query = tbl_object\
                        .select()\
                        .where(tbl_object.username == username, tbl_object.created_at> start_date)\
                        .order_by(-tbl_object.created_at)\
                        


    elif end_date and not start_date:
        query = tbl_object\
                        .select()\
                        .where(tbl_object.username == username, tbl_object.created_at < end_date)\
                        .order_by(-tbl_object.created_at)\
        


    else: # not  start_date and  not end_date

        query = tbl_object\
                .select()\
                .where(tbl_object.username == username)\
                .order_by(-tbl_object.created_at)\


    return  query.offset(skip).limit(limit).dicts(), query.count()




@aiomisc.threaded #makes function asynchronous
def match_text(tbl_object, username,  indexed_obj, matching_string, start_date, end_date, skip, limit,  time=None):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """


    if start_date and end_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.tweet_hash == indexed_obj.tweet_hash))\
                .where(tbl_object.username == username, 
                    indexed_obj.match(matching_string) , 
                    tbl_object.created_at> start_date, 
                    tbl_object.created_at < end_date )\
                .order_by(-tbl_object.created_at)

                
        

    elif start_date and not end_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.tweet_hash == indexed_obj.tweet_hash))\
                .where(tbl_object.username == username, 
                    indexed_obj.match(matching_string), 
                    tbl_object.created_at> start_date)\
                .order_by(-tbl_object.created_at)

        


    elif end_date and not start_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.tweet_hash == indexed_obj.tweet_hash))\
                .where(indexed_obj.match(matching_string),
                    tbl_object.username == username,
                 tbl_object.created_at < end_date)\
                .order_by(-tbl_object.created_at)



    else: # not  start_date and  not end_date
        query = tbl_object\
                    .select()\
                    .join(indexed_obj, on=(tbl_object.tweet_hash == indexed_obj.tweet_hash))\
                    .where(tbl_object.username == username, 
                    indexed_obj.match(matching_string))\


    return  query.offset(skip).limit(limit).dicts(), query.count()




@aiomisc.threaded #makes function asynchronous
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
