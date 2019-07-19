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



@GITHUB_BP.post('/parse')
async def parse(request):
    """
    """

    request.app.config.VALIDATE_FIELDS(["path", "override"], request.json)

    dest_directory  = f"{request.app.config.RAW_DATA_PATH}/github"

    if os.path.exists(dest_directory):
        if not request.json["override"]:
            raise APIBadRequest("GITHUB Data already exists")

    if request.json["path"].endswith("zip"):
        shutil.unpack_archive(request.json["path"], extract_dir=dest_directory, format=None)

    elif request.json["path"].endswith(".gz"):
        t = tarfile.open(request.json["path"], 'r')
        t.extractall(dest_directory)


    else:
        raise APIBadRequest("Unknown format")

    logger.info(f"THe request was successful with github path {request.json['path']}")

    return response.json(
        {
        'error': False,
        'success': True,
        })









