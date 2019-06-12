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




@FACEBOOK_BP.post('/parse')
async def facebook_download_parse(request):
    """
    """
    required_fields = ["path", "override"]
    request.app.config.VALIDATE_FIELDS(["path", "override"], request.json)

    if not request.json["path"].endswith("zip"):
        raise APIBadRequest("This path is not a valid facebook zip file")


    facebook_zip_file_path = request.json["path"]
    

    dest_directory  = f"{request.app.config.RAW_DATA_PATH}/facebook"

    if os.path.exists(dest_directory):
        if not request.json["override"]:
            raise APIBadRequest("Facebook Data already exists")



    logging.warning (f"ZIP Directory is {facebook_zip_file_path}")
    logging.warning (f"Destination Directory is {dest_directory}")
    logger.info(f"THe request was successful with path {request.json['path']}")

    # shutil.copyfile(request.json["path"], dest_directory)
    # zip_ref = zipfile.ZipFile(facebook_zip_file_path, 'r')
    # zip_ref.extractall(dest_directory)
    # zip_ref.close()

    shutil.unpack_archive(request.json["path"], extract_dir=dest_directory, format=None)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
        })









