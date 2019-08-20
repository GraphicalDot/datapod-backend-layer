
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
import datetime
import humanize
from utils.utils import revoke_time_stamp, update_tokens, id_token_validity, creation_date, modification_date
from .back import Backup, S3Backup
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

BACKUP_BP = Blueprint("backup", url_prefix="/backup")

from database_calls.credentials import store_credentials, get_credentials, update_id_and_access_tokens,\
            update_mnemonic,   update_datasources_status
    
import config
from functools import wraps
from jose import jwt, JWTError 
import pytz
import datetime
import dateutil
import hashlib
import requests
import json
from utils.utils import async_wrap

@BACKUP_BP.get('/settings')
#async def make_backup(request, ws):
async def backup_settings(request):
    request.app.config.VALIDATE_FIELDS(["time", "backup_frequency", "number_of_backups", "upload_speed", "download_speed"], request.json)



@BACKUP_BP.get('/backups_list')
#async def make_backup(request, ws):
async def backups_list(request):

    result = await backup_list_info(request.app.config)

    return response.json({
            "error": False,
            "success": True, 
            "data": result,
            "message": None
        })


@async_wrap
def backup_list_info(config):
    result = []
    def get_dir_size(dirpath):
        all_files = [os.path.join(basedir, filename) for basedir, dirs, files in os.walk(dirpath) for filename in files]
        _date = creation_date(all_files[0])
        files_and_sizes = [os.path.getsize(path) for path in all_files]
        return  humanize.naturalsize(sum(files_and_sizes)), _date



    for (path, dirs, files) in os.walk(config.BACKUP_PATH):
        for _dir in dirs:
            dirpath = os.path.join(path, _dir)
            size, date = get_dir_size(dirpath)
            result.append({"name": _dir, "size": size, "date": date})
    
    return result
    





@BACKUP_BP.post('/directory_info')
#async def make_backup(request, ws):
async def backups_list(request):
    request.app.config.VALIDATE_FIELDS(["dirpath"], request.json)

    if not os.path.isdir(request.json["dirpath"]):
        raise APIBadRequest("Not a valid directory path")


    all_files = ( os.path.join(basedir, filename) for basedir, dirs, files in os.walk(request.json["dirpath"]) for filename in files)
    files_and_sizes = [{"path": path, "size":  humanize.naturalsize(os.path.getsize(path)), "modified": modification_date(path), "created": creation_date(path)} for path in all_files]
    return response.json(
        {
            "error": False,
            "success": True, 
            "data": files_and_sizes,
            "message": None
        }

    )





#@id_token_validity()
async def aws_temp_creds(config, id_token, username):

    r = requests.post(config.AWS_CREDS, data=json.dumps({
                    "id_token": id_token}))
    
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    
    return result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]

    



async def backup_upload(config, id_token):
    # Method to handle the new backup and sync with s3 
    update_datasources_status(config.DATASOURCES_TBL , "BACKUP", "backup" , config.DATASOURCES_CODE["BACKUP"], "Backup in Progress", "PROGRESS")

    archival_object = datetime.datetime.utcnow()
    archival_name = archival_object.strftime("%B-%d-%Y_%H-%M-%S")

    backup_instance = Backup(config)
    await backup_instance.create(archival_name)

    
    instance = await S3Backup(config, id_token)
    await instance.sync_backup()
    update_datasources_status(config.DATASOURCES_TBL , "BACKUP", "backup" , config.DATASOURCES_CODE["BACKUP"], "Backup Completed", "COMPLETED")
    await backup_instance.send_sse_message("COMPLETED")

    return 


@BACKUP_BP.get('/make_backup')
@id_token_validity()
async def make_backup(request):
    """
    ##TODO ADD entries to BACKUP_TBL
    """


    try:
            
        request.app.add_task(backup_upload(request.app.config, request["user_data"]["id_token"]))

        # new_log_entry = request.app.config.LOGS_TBL.create(timestamp=archival_object, message=f"Archival was successful on {archival_name}", error=0, success=1)
        # new_log_entry.save()

    except Exception as e:
        logger.error(e.__str__())
        # new_log_entry = request.app.config.LOGS_TBL.create(timestamp=archival_object, message=f"Archival failed because of {e.__str__()} on {archival_name}", error=1, success=0)
        # new_log_entry.save()


    return response.json(
        {
        'error': False,
        'success': True,
        })