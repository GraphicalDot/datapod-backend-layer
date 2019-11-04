import json
import os
import asyncio
import functools
from .db_calls import update_status, get_stats, get_stats, update_stats, store, store_account
from loguru import logger
from dputils.utils import async_wrap, send_sse_message
from collections import Counter
from .variables import DATASOURCE_NAME
from glob import glob
import subprocess
import datetime

def dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')



def files_count(dirpath):
    return sum([len(files) for r, d, files in os.walk(dirpath)])

async def _parse(config, path, username, checksum):
    
    #if the user enetered a username which is different from the real username
    # username = await get_username(config, path)

    logger.success(f"The twitter username is {username}")
    
    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"] , DATASOURCE_NAME, username, "PROGRESS")

    number_of_tweets, common_hashtags, common_user_mentions  = await read_tweet(config, path, username, checksum)

    account_display_name = await account(config, path, number_of_tweets, common_hashtags, common_user_mentions, username, checksum)


    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, username, "COMPLETED")




    ##updating stats table with relevant information
    target_dir = os.path.join(config["RAW_DATA_PATH"], DATASOURCE_NAME, username)

    logger.success(f"This is the target dir {target_dir}")
    size = dir_size(path)
    data_items = files_count(path) 
    logger.success(f"username == {path} size == {size} dataitems == {data_items}")

    await update_stats(config[DATASOURCE_NAME]["tables"]["stats_table"], 
            DATASOURCE_NAME, 
                username, data_items, size, "weekly", "auto", datetime.datetime.utcnow() + datetime.timedelta(days=7) ) 



    return 




async def get_username(config, path):
    file_path = os.path.join(path, "account.js")
    with open(file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)

    account = jsonObj[0].get("account")
    return account.get("username")


async def read_tweet(config, path, username, checksum):
    tweets_file_path = os.path.join(path, "tweet.js")
    with open(tweets_file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)

    i = 100/len(jsonObj)


    hash_tag_list, user_mention_list = [], []
    for num, tweet in enumerate(jsonObj):
        tweet.update({"tbl_object": config[DATASOURCE_NAME]["tables"]["tweet_table"],
                    "indexed_tbl_object": config[DATASOURCE_NAME]["tables"]["indexed_tweet_table"],
                    "username": username,
                    "checksum": checksum})

        hash_tag, user_mention = await  store(**tweet)
        hash_tag_list.extend(hash_tag)
        user_mention_list.extend(user_mention)

        res = {"message": "Processing tweet", "percentage": int(i*(num+1))}
        #await send_sse_message(config, config.TWITTER_SSE_TOPIC, res)
        await config["send_sse_message"](config, DATASOURCE_NAME, res)

    # loop = asyncio.get_event_loop()
    # tasks = [store(**args)  for args in jsonObj]
    # loop.run_until_complete(asyncio.wait(tasks))
    # loop.close()

    # _, _ = await asyncio.wait(
    #         fs=[loop.run_in_executor(executor, 
    #                 functools.partial(q_images_db.store, **args)) for args in images_data],
    #         return_when=asyncio.ALL_COMPLETED
    #     )
    logger.info(f"User Mention list {user_mention_list}")
    logger.info(f"Hash tag list list {hash_tag_list}")


    return num, most_common(hash_tag_list), most_common(user_mention_list)


async def account(config, path, number_of_tweets, common_hashtags, common_user_mentions, username, checksum):
    file_path = os.path.join(path, "account.js")
    with open(file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)

    account_data = jsonObj[0].get("account")
    account_data.update({"follower_count":  await followers(path)})
    account_data.update({"following_count":  await following(path)})
    account_data.update({"list_created":  await list_created(path)})
    account_data.update({"list_subscribed": await  list_subscribed(path)})
    account_data.update({"list_member":  await list_member(path)})
    account_data.update({"likes":  await likes(path)})
    account_data.update({"contacts":  await contacts(path)})
    account_data.update({"tweets":  number_of_tweets})
    account_data.update({"common_hashtags":  json.dumps(common_hashtags)})
    account_data.update({"common_user_mentions":  json.dumps(common_user_mentions)})


    if account_data:
        account_data.update({"tbl_object": config[DATASOURCE_NAME]["tables"]["account_table"],
                    "username": username, 
                    "checksum": checksum})
        await store_account(**account_data)
    else:
        return None

    return account_data.get("accountDisplayName")


async def followers(path):
    result, count = await read_file(path, "follower.js")
    logger.info(f"Number of followers {result}")
    return count
    


async def following(path):
    result, count = await read_file(path, "following.js")
    return count


async def list_created(path):
    result, count = await read_file(path, "lists-created.js")
    return count


async def list_subscribed(path):
    result, count = await read_file(path, "lists-subscribed.js")
    return count


async def list_member( path):
    result, count = await read_file(path, "lists-member.js")
    return count

async def likes( path):
    result, count = await read_file(path, "like.js")
    return count


async def contacts(path):
    result, count = await read_file(path, "contact.js")
    return count


async def read_file(path, filename):
    file_path = os.path.join(path, filename)
    with open(file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    _list = json.loads(data)
    try:
        return  _list, len(_list)
    except Exception as e:
        logger.error(e)
        return  _list, 0
    return 


def most_common(array, items=10):
    if len(array) > 0:
        res = Counter(array)
        return res.most_common()[0: items]
    return []