import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
from .facebook_ds import data_parse
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
FACEBOOK_BP = Blueprint("facebook", url_prefix="/facebook")


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise APIBadRequest("Improper JSON format")




    #await save_instagram(allposts, instagram_path, app.config.db_dir_path)
    return 

@FACEBOOK_BP.post('/parse')
async def facebook_download_parse(request):
    """
    """


    
    required_fields = ["path"]
    validate_fields(required_fields, request.json)
    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    if not request.json["path"].endswith("zip"):
        raise APIBadRequest("This path is not a valid mbox file")


    facebook_zip_file_path = request.json["path"]
    

    dest_directory  = f"{request.app.config.user_data_path}/facebook"


    logging.warning (f"ZIP Directory is {facebook_zip_file_path}")
    logging.warning (f"Destination Directory is {dest_directory}")
    logger.info(f"THe request was successful with path {request.json['path']}")
    # shutil.copyfile(request.json["path"], dest_directory)
    # zip_ref = zipfile.ZipFile(facebook_zip_file_path, 'r')
    # zip_ref.extractall(dest_directory)
    # zip_ref.close()

    shutil.unpack_archive(request.json["path"], extract_dir=dest_directory, format=None)

    #os.remove(facebook_zip_file_path)

    #await data_parse(request.app, dest_directory)
    #request.app.add_task(periodic(request.app, instagram_object))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
        })









