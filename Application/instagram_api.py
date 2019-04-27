

from InstagramAPI import InstagramAPI
from database_calls import get, insert, create_db_instance, close_db_instance
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncio
import os, sys
from kivy.logger import Logger
from PIL import Image


INSTAGRAM_KEY_NAME = "instagram"
INSTAGRAM_IMG_THUMBNAIL = "instagram_img_thumbnail"
INSTAGRAM_IMG_OTHER = "instagram_img_other"
INSTAGRAM_DIR = "instagram_images"



if getattr(sys, 'frozen', False):
    # frozen
    dirpath = os.path.dirname(sys.executable)
else:
    # unfrozen
    #dir_ = os.path.dirname(os.path.realpath(__file__))
    dirpath = os.getcwd()




def save_on_filesystem(image_tuple):
    image_id = image_tuple[0]

    for image in image_tuple[1]:
        name = dirpath + "/"+ INSTAGRAM_DIR + "/"+ image_id + "-" + str(image["width"]) + "."+image["content_type"].split("/")[-1]
        with open(name, "wb") as f:
            f.write(image["data"])
    return 

def get_instagram_thumbnails():
    thumbnails = get(INSTAGRAM_IMG_THUMBNAIL)
    Logger.info(thumbnails)
    return thumbnails

def save_instagram(posts):

    ##filter out the url and their id from the posts 
    ##right now fecthing only the (240, 240) size image 
    ##from the cdn
    url_list = instagram_image_thumbnails(posts)
    Logger.info(url_list)

    ##fetch alll images from the instagram cdn 
    ##will be a list of tuples, with first entry as 
    ##the instagram id and the second entry will be 
    # a list of dictionaries, with each ditionary 
    # with keys [width, height, url, content_type, data]     

    image_data_list = get_instagram_images(url_list)

    ##saving these two datas differently, saving
    ##thumbnails differently and rest of the pizel images 
    ##differently 
    instagram_img_thumbnail= []
    instagram_img_other = []

    for (image_id, image_likes, image_top_likers, image_data) in image_data_list:
        for image in image_data:
            image.update({"id": image_id, "likes": image_likes, "top_likers": image_top_likers})
            if image["width"] == 240:
                instagram_img_thumbnail.append(image)
            else:
                instagram_img_other.append(image)

    Logger.warning(instagram_img_thumbnail[0].keys())
    Logger.warning(instagram_img_other[0].keys())
    db = create_db_instance()
    insert(INSTAGRAM_KEY_NAME, posts, db)
    insert(INSTAGRAM_IMG_THUMBNAIL, instagram_img_thumbnail, db)
    insert(INSTAGRAM_IMG_OTHER, instagram_img_other, db)
    close_db_instance(db)
    Logger.info("Insert operations for instgram completed")
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
        Logger.error("Instagram posts array must be a list")
    
    url_list = []
    for post in posts: 
        _id = post["id"] 
        url_list.append((_id, post["like_count"], post["top_likers"], post["image_versions2"]["candidates"])) 
    return url_list

def instagram_login(username, password):
    Logger.info(f"Instagram username {username}")
    Logger.info(f"Instagram password {password}")
    instagram_object = InstagramAPI(username, password)
    Logger.info(f"Instagram object {instagram_object}")
    
    status = instagram_object.login()
    
    Logger.info(status)
    if not status:
        raise Exception()
    return instagram_object


def get_all_posts(instagram_object, myposts=[]):
    has_more_posts = True
    max_id=""

    while has_more_posts:
        instagram_object.getSelfUserFeed(maxid=max_id)
        if instagram_object.LastJson['more_available'] is not True:
            has_more_posts = False #stop condition
            Logger.info("No More instagram posts for this user")
        
        max_id = instagram_object.LastJson.get('next_max_id','')
        myposts.extend(instagram_object.LastJson['items']) #merge lists
        time.sleep(2) # Slows the script down to avoid flooding the servers 
    
    return max_id, myposts 





async def get_instagram_image(urls):
    Logger.info(f"NOw fetching {urls}")
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
                    Logger.error("FAILURE::{0}".format(url_data["url"]))
                    return None
                response.close()


        name = dirpath + "/"+ INSTAGRAM_DIR + "/"+ image_id + "-" + str(url_data["width"]) + "."+response.content_type.split("/")[-1]
        with open(name, "wb") as f:
            f.write(data)

        result.append({
                "width": url_data["width"], "height": url_data["height"], 
                "url": url_data["url"], 
                "content_type": response.content_type,
                "disk_name": name

        })


    return (image_id, urls[1], urls[2], result)


def get_instagram_images(pages):

    loop = asyncio.get_event_loop()
    # for page in pages:
    #     tasks.append(loop.create_task(print_preview(page)))

    #executor = ThreadPoolExecutor(max_workers=10)
    #tasks = [loop.run_in_executor(executor, get_instagram_image, url) for url in pages]
    tasks = [loop.create_task(get_instagram_image(url)) for url in pages]
    several_futures = asyncio.gather(*tasks)
    results = loop.run_until_complete(several_futures)

    #loop.run_until_complete(asyncio.wait(tasks))
    return results