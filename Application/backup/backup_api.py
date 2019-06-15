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
from .back import Backup
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

BACKUP_BP = Blueprint("backup", url_prefix="/backup")



@BACKUP_BP.get('/make_backup')
async def make_backup(request):
    """
    """

    instance = Backup(request)
    instance.create()

    # if os.path.exists(dest_directory):
    #     if not request.json["override"]:
    #         raise APIBadRequest("GITHUB Data already exists")

    # if request.json["path"].endswith("zip"):
    #     shutil.unpack_archive(request.json["path"], extract_dir=dest_directory, format=None)

    # elif request.json["path"].endswith(".gz"):
    #     t = tarfile.open(request.json["path"], 'r')
    #     t.extractall(dest_directory)


    # else:
    #     raise APIBadRequest("Unknown format")

    # logger.info(f"THe request was successful with crypto path {request.json['path']}")

    return response.json(
        {
        'error': False,
        'success': True,
        })