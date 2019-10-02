
import json
import os
from database_calls.twitter.calls import store, store_account
import asyncio
import functools
from database_calls.credentials import update_datasources_status, datasource_status
from loguru import logger
from utils.utils import async_wrap, send_sse_message



async def _parse(config, path):
    update_datasources_status(config.DATASOURCES_TBL , "TWITTER", None, config.DATASOURCES_CODE["TWITTER"], "Twitter data aprsing has been completed", "PROGRESS")
    
    number_of_tweets = await read_tweet(config, path)
    account_display_name = await account(config, path, number_of_tweets)


    update_datasources_status(config.DATASOURCES_TBL , "TWITTER", account_display_name, config.DATASOURCES_CODE["TWITTER"], "Twitter data aprsing has been completed", "COMPLETED")
    return 






async def read_tweet(config, path):
    tweets_file_path = os.path.join(path, "tweet.js")
    with open(tweets_file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)

    i = 100/len(jsonObj)

    for num, tweet in enumerate(jsonObj):
        tweet.update({"tbl_object": config.TWITTER_TBL, "indexed_tbl_object": config.TWITTER_INDEXED_TBL})
        await  store(**tweet)

        res = {"message": "Processing tweet", "percentage": int(i*(num+1))}
        await send_sse_message(config, config.TWITTER_SSE_TOPIC, res)

    # loop = asyncio.get_event_loop()
    # tasks = [store(**args)  for args in jsonObj]
    # loop.run_until_complete(asyncio.wait(tasks))
    # loop.close()

    # _, _ = await asyncio.wait(
    #         fs=[loop.run_in_executor(executor, 
    #                 functools.partial(q_images_db.store, **args)) for args in images_data],
    #         return_when=asyncio.ALL_COMPLETED
    #     )
    return num


async def account(config, path, number_of_tweets):
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

    if account_data:
        logger.info(f"Account table for Twitter  {config.TWITTER_ACC_TBL}")
        account_data.update({"tbl_object": config.TWITTER_ACC_TBL})
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