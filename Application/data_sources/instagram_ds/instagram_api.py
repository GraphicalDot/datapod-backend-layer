
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .instagram_data import save_instagram, instagram_login, get_all_posts
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
INSTAGRAM_BP = Blueprint("instagram", url_prefix="/instagram")

async def periodic(app, instagram_object):
    ##add this if this has to executed periodically
    ##while True:
   
    _, allposts = get_all_posts(instagram_object, myposts=[])
    print (allposts)
    instagram_path = os.path.join(app.config.user_data_path, "instagram/images") 
    if not os.path.exists(instagram_path):
        logger.warning(f"Path doesnt exists creating {instagram_path}")
        os.makedirs(instagram_path) 
    await save_instagram(allposts, instagram_path, app.config.db_dir_path)
    return 

@INSTAGRAM_BP.post('/fetch_data')
async def instagram_fetch_images(request):
    """
    """
    request.app.config.VALIDATE_FIELDS(["username", "password"], request.json)

    
    instagram_object = instagram_login(request.json["username"], request.json["password"])
    if not instagram_object:
        raise APIBadRequest("Wrong username and password for instagram")


    request.app.add_task(periodic(request.app, instagram_object))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Instagram login has been sucessful"
        })
