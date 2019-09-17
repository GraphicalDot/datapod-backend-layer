
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
    
    account_display_name = await account(config, path)
    await read_tweet(config, path)


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
    return 


async def account(config, path):
    file_path = os.path.join(path, "account.js")
    with open(file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)

    account_data = jsonObj[0].get("account")
    logger.error(account_data)
    if account_data:

        account_data.update({"tbl_object": config.TWITTER_ACC_TBL})
        await store_account(**account_data)
    else:
        return None

    return account_data.get("accountDisplayName")