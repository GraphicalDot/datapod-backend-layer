
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
import datetime

from utils.utils import revoke_time_stamp, update_tokens, id_token_validity
from .back import Backup, S3Backup
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

BACKUP_BP = Blueprint("backup", url_prefix="/backup")

from database_calls.credentials import store_credentials, get_credentials, update_id_and_access_tokens,\
            update_mnemonic
    
import config
from functools import wraps
from jose import jwt, JWTError 
import pytz
import datetime
import dateutil
import hashlib
import requests
import json

@BACKUP_BP.get('/settings')
#async def make_backup(request, ws):
async def backup_settings(request):
    request.app.config.VALIDATE_FIELDS(["time", "backup_frequency", "number_of_backups", "upload_speed", "download_speed"], request.json)










#@id_token_validity()
async def aws_temp_creds(config, id_token, username):

    r = requests.post(config.AWS_CREDS, data=json.dumps({
                    "id_token": id_token}))
    
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    
    return result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]

    

@BACKUP_BP.get('/aws_creds')
@id_token_validity()
#async def make_backup(request, ws):
async def aws_creds(request):
    identity_id, access_key, secret_key, session_token =  await aws_temp_creds(request.app.config, request["user_data"]["id_token"], request["user_data"]["username"])
    async for msg in S3Backup.sync_backup(request.app.config, identity_id, access_key, secret_key, session_token):
        logger.info(msg)
    return response.json({"error": False, "sucess": True})



async def backup_upload(config, id_token):
    # Method to handle the new backup and sync with s3 
    
    # archival_object = datetime.datetime.utcnow()
    # archival_name = archival_object.strftime("%B-%d-%Y_%H-%M-%S")

    # instance = Backup(config)
    # await instance.create(archival_name)

    #await instance.create(archival_name)
    
    instance = await S3Backup(config, id_token)
    await instance.sync_backup()

    #request.app.add_task(



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