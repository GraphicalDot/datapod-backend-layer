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
import datetime

from .back import Backup
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

BACKUP_BP = Blueprint("backup", url_prefix="/backup")




@BACKUP_BP.get('/settings')
#async def make_backup(request, ws):
async def backup_settings(request):
    request.app.config.VALIDATE_FIELDS(["time", "backup_frequency", "number_of_backups", "upload_speed", "download_speed"], request.json)



@BACKUP_BP.get('/make_backup')
#async def make_backup(request, ws):
async def make_backup(request):
    """
    ##TODO ADD entries to BACKUP_TBL
    """
    archival_object = datetime.datetime.utcnow()
    archival_name = archival_object.strftime("%B-%d-%Y_%H-%M-%S")

    try:
        instance = Backup(request)
        async for msg in instance.create(archival_name):
            #logging.info(msg)
            #await ws.send(i)
            pass
        new_log_entry = request.app.config.LOGS_TBL.create(timestamp=archival_object, message=f"Archival was successful on {archival_name}", error=0, success=1)
        new_log_entry.save()

    except Exception as e:
        logging.error(e.__str__())
        new_log_entry = request.app.config.LOGS_TBL.create(timestamp=archival_object, message=f"Archival failed because of {e.__str__()} on {archival_name}", error=1, success=0)
        new_log_entry.save()


    return response.json(
        {
        'error': False,
        'success': True,
        })