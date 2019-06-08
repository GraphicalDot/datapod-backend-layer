import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import zipfile
import tarfile
import gzip
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
GITHUB_BP = Blueprint("github", url_prefix="/github")


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise APIBadRequest("Improper JSON format")




    #await save_instagram(allposts, instagram_path, app.config.db_dir_path)
    return 

@GITHUB_BP.post('/parse')
async def parse(request):
    """
    """

    logger.info("THe file began execution")
    
    required_fields = ["path"]
    validate_fields(required_fields, request.json)
    dest_directory  = f"{request.app.config.user_data_path}/github"

    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    logging.warning (f"Target Directory is {request.json['path']}")
    logging.warning (f"Destination Directory is {dest_directory}")
    
    if not os.path.exists(dest_directory):
        os.makedirs(dest_directory)

    if request.json["path"].endswith("zip"):
        shutil.unpack_archive(request.json["path"], extract_dir=dest_directory, format=None)

    elif request.json["path"].endswith(".gz"):
        t = tarfile.open(request.json["path"], 'r')
        t.extractall(dest_directory)

        # with gzip.open(request.json["path"], 'r') as f_in, open(dest_directory, 'wb') as f_out:
        #     shutil.copyfileobj(f_in, f_out)

    else:
        raise APIBadRequest("Unknown format")

    logger.info(f"THe request was successful with github path {request.json['path']}")

    return response.json(
        {
        'error': False,
        'success': True,
        })









