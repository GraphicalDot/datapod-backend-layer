
import json
import os
from database_calls.twitter.calls import store
import asyncio
import functools




async def _parse(config, path):
    await read_tweet(config, path)
    return 






async def read_tweet(config, path):
    tweets_file_path = os.path.join(path, "tweet.js")
    with open(tweets_file_path, 'rb') as f: 
        lines = f.read().decode().replace("\n", "") 

    data = lines[lines.find('[') : lines.rfind(']')+1]
    jsonObj = json.loads(data)
    for tweet in jsonObj:
        tweet.update({"tbl_object": config.TWITTER_TBL, "indexed_tbl_object": config.TWITTER_INDEXED_TBL})
        await  store(**tweet)


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
