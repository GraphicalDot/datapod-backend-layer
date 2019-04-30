#-*- coding:utf-8 -*- 




from InstagramAPI import InstagramAPI
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncio
import os, sys
from PIL import Image
import datetime
import pytz
from pathlib import Path

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


"""

sys.path.append(Path.cwd().parent.parent)


print (Path.cwd().parent.parent)
print (sys.path)
o= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print (o)
print (os.path.dirname(o))
oo = os.path.dirname(o)

sys.path.append(oo)
print (sys.path)
"""
parent_module_path= os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))
print (parent_module_path)

sys.path.append(parent_module_path)

from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key

#from database_calls import database_calls 
#import create_db_instance, close_db_instance, get_key, insert_key






def indian_time_stamp(naive_timestamp=None):
    tz_kolkata = pytz.timezone('Asia/Kolkata')
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp.strftime(time_format + " %Z%z")





async def save_instagram(posts, data_path, db_dir_path):

    ##filter out the url and their id from the posts 
    ##right now fecthing only the (240, 240) size image 
    ##from the cdn
    url_list = instagram_image_thumbnails(posts)
    logger.info(url_list)

    ##fetch alll images from the instagram cdn 
    ##will be a list of tuples, with first entry as 
    ##the instagram id and the second entry will be 
    # a list of dictionaries, with each ditionary 
    # with keys [width, height, url, content_type, data]     

    image_data_list = await get_instagram_images(url_list, data_path)

    ##saving these two datas differently, saving
    ##thumbnails differently and rest of the pizel images 
    ##differently 
    instagram_img_thumbnail= []
    instagram_img_other = []

    for (image_id, image_likes, image_top_likers, image_data) in image_data_list:
        for image in image_data:
            image.update({"id": image_id, "likes": image_likes, "top_likers": image_top_likers, "source": "instagram"})
            if image["width"] == 240:
                instagram_img_thumbnail.append(image)
            else:
                instagram_img_other.append(image)


    db_instance = create_db_instance(db_dir_path)
    stored_value = get_key("logs", db_instance)

    value = [{"date": indian_time_stamp(), 
            "status": "success", 
            "message": "Instagram data has been pulled successfully"}]
    
    if stored_value:
        value = value+stored_value  

    logger.info(f"value stored against logs is {value}")
    insert_key("logs", value, db_instance)

    insert_key("instagram_images", instagram_img_other, db_instance)
    insert_key("instagram_images_thumbnails", instagram_img_thumbnail, db_instance)


    stored_value = get_key("services", db_instance)

    value = [{"time": indian_time_stamp(), 
            "service": "instagram", 
            "message": f"{len(instagram_img_other)} images present"}]
    
    if stored_value:
        
        for entry in stored_value:
            if entry.get("service") == "instagram":
                break
        stored_value.pop(entry)
        stored_value.append(value)
    else:
        stored_value = value
    insert_key("services", stored_value, db_instance)

    close_db_instance(db_instance)


    # db = create_db_instance()
    # insert(INSTAGRAM_KEY_NAME, posts, db)
    # insert(INSTAGRAM_IMG_THUMBNAIL, instagram_img_thumbnail, db)
    # insert(INSTAGRAM_IMG_OTHER, instagram_img_other, db)
    # close_db_instance(db)
    # logger.info("Insert operations for instgram completed")
    return 





def instagram_image_thumbnails(posts=None):
    """
    Returns url_list in the form of tuples, where first element is 
    the id of the image and then a value as a list of different 
    pixels image
    [('2019976889439294312_8078437896',
        [{'width': 648,
            'height': 648,
            'url': ',
        {'width': 240,
            'height': 240,
            'url': ',
        }]), .......]

    """
    if not posts:
        posts = get(INSTAGRAM_KEY_NAME)
    if not isinstance(posts, list):
        logger.error("Instagram posts array must be a list")
    
    url_list = []
    for post in posts: 
        _id = post["id"] 
        url_list.append((_id, post["like_count"], post["top_likers"], post["image_versions2"]["candidates"])) 
    return url_list

def instagram_login(username, password):
    instagram_object = InstagramAPI(username, password)
    
    status = instagram_object.login()
    
    logger.info(f"Instagram login status {status}")
    if not status:
        return False
    return instagram_object


def get_all_posts(instagram_object, myposts=[]):
    has_more_posts = True
    max_id=""

    while has_more_posts:
        instagram_object.getSelfUserFeed(maxid=max_id)
        if instagram_object.LastJson['more_available'] is not True:
            has_more_posts = False #stop condition
            logger.info("No More instagram posts for this user")
        
        max_id = instagram_object.LastJson.get('next_max_id','')
        myposts.extend(instagram_object.LastJson['items']) #merge lists
        time.sleep(2) # Slows the script down to avoid flooding the servers 
    
    return max_id, myposts 





async def get_instagram_image(urls, data_path):
    logger.info(f"NOw fetching {urls}")
    ##urls [1] is like_count
    ##urls [2] is top likers
    result = []
    image_id = "instagram-"+ urls[0]
    image_url_list = urls[-1]
    for url_data in image_url_list:
        async with aiohttp.ClientSession() as session:
            # create get request
            async with session.get(url_data["url"]) as response:
                # wait for response
                data = await response.read()
                # print first 3 not empty lines
                if response.status != 200:
                    logger.error("FAILURE::{0}".format(url_data["url"]))
                    return None
                response.close()


        if url_data["width"] == 240:
            name = data_path + "/"+ image_id + "-" + "thumbnail" + "."+response.content_type.split("/")[-1]
        else:
            name = data_path + "/"+ image_id  + "."+response.content_type.split("/")[-1]


        with open(name, "wb") as f:
            f.write(data)

        result.append({
                "width": url_data["width"], "height": url_data["height"], 
                "url": url_data["url"], 
                "content_type": response.content_type,
                "path": name

        })


    return (image_id, urls[1], urls[2], result)


async def get_instagram_images(pages, data_path):

    # for page in pages:
    #     tasks.append(loop.create_task(print_preview(page)))

    #executor = ThreadPoolExecutor(max_workers=10)
    #tasks = [loop.run_in_executor(executor, get_instagram_image, url) for url in pages]
    tasks = [get_instagram_image(url, data_path) for url in pages]
    
    #several_futures = asyncio.gather(*tasks)
    #results = loop.run_until_complete(several_futures)
    results = await asyncio.gather(*tasks)
    #await asyncio.wait(tasks)
    #loop.run_until_complete(asyncio.wait(tasks))
    return results 

if __name__ == "__main__":
    instagram_object = instagram_login(username, password)
    max_id, allposts = get_all_posts(instagram_object, myposts=[])
    print (allposts)
    instagram_path = "/home/feynman/Programs/datapod-backend-layer/Application/userdata/instagram/images"
    db_dir__path = "/home/feynman/Programs/datapod-backend-layer/Application/database"
    if not os.path.exists(instagram_path):
        logger.warning(f"Path doesnt exists creating {instagram_path}")
        os.makedirs(instagram_path) 
    save_instagram(allposts, instagram_path, db_dir__path)

