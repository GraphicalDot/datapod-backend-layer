from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
import datetime
import humanize
from .utils import Backup, S3Backup
from loguru import logger
from .db_calls import get_stats, get_status,  delete_status, update_status


from ..shared.utils import  creation_date, modification_date

import datetime
import dateutil
import hashlib
import requests
import json
import aiomisc
from .variables import DATASOURCE_NAME

async def backup_settings(request):
    request.app.config.VALIDATE_FIELDS(["time", "backup_frequency", "number_of_backups", "upload_speed", "download_speed"], request.json)




async def stats(request):
    res = await get_stats(request.app.config[DATASOURCE_NAME]["tables"]["stats_table"])
    return res


    

async def status(request):
    res = await get_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"])
    return res




#async def make_backup(request, ws):
async def backup_list(request):

    result = await backup_list_info(request.app.config)

    return response.json({
            "error": False,
            "success": True, 
            "data": result,
            "message": None
        })


@aiomisc.threaded_separate
def backup_list_info(config):
    result = []
    def get_dir_size(dirpath):
        all_files = [os.path.join(basedir, filename) for basedir, dirs, files in os.walk(dirpath) for filename in files]
        if len(all_files) >0:
            _date = creation_date(all_files[0])
        else:
            _date = None
        files_and_sizes = [os.path.getsize(path) for path in all_files]
        return  humanize.naturalsize(sum(files_and_sizes)), _date


    for (path, dirs, files) in os.walk(config.BACKUP_PATH):
        if len(dirs) != 0:
            for _dir in dirs:
                dirpath = os.path.join(path, _dir)
                size, date = get_dir_size(dirpath)
                result.append({"name": _dir, "size": size, "date": date})


    return result
    





# #async def make_backup(request, ws):
# async def backups_list(request):
#     request.app.config.VALIDATE_FIELDS(["dirpath"], request.json)

#     if not os.path.isdir(request.json["dirpath"]):
#         raise APIBadRequest("Not a valid directory path")


#     all_files = ( os.path.join(basedir, filename) for basedir, dirs, files in os.walk(request.json["dirpath"]) for filename in files)
#     files_and_sizes = [{"path": path, "size":  humanize.naturalsize(os.path.getsize(path)), "modified": modification_date(path), "created": creation_date(path)} for path in all_files]
#     return response.json(
#         {
#             "error": False,
#             "success": True, 
#             "data": files_and_sizes,
#             "message": None
#         }

#     )



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
 
    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "PROGRESS",  dest_path, request.json["path"])

    archival_object = datetime.datetime.utcnow()
    archival_name = archival_object.strftime("%B-%d-%Y_%H-%M-%S")

    backup_instance = Backup(config)
    await backup_instance.create(archival_name)

    
    instance = await S3Backup(config, id_token)
    await instance.sync_backup()

    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "COMPLETED",  dest_path, request.json["path"])

    await backup_instance.send_sse_message("COMPLETED")

    return 


async def start_fresh_backup(request):
    """
    ##TODO ADD entries to BACKUP_TBL
    """
    ##This has a rare chance of happening, that users reach here and doesnt have mnemonic in the database but have mnemonic in the cloud
    creds = (request.app.config.CREDENTIALS_TBL)
    if not creds.get("mnemonic"):
        raise APIBadRequest("User Mnemonic is not present", 403)

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