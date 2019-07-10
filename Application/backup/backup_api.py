
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




def id_token_validity():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            #is_authorized = check_request_for_authorization_status(request)

            result = get_credentials(config.config_object.CREDENTIALS_TBL)
            logger.info(f"Data from the credential table in id_token_validity decorator {result}")
            if not result:
                logger.error("Credentials aren't present, Please Login again")
                raise APIBadRequest("Credentials aren't present, Please Login again")

            try:
                id_token = result["id_token"].decode()
                refresh_token = result["refresh_token"].decode()
                username = result["username"]
            
            except Exception as e:
                
                logger.error("User must have signed out, Please Login again")
                raise APIBadRequest("Please Login again")


            payload = jwt.get_unverified_claims(id_token)

            time_now = datetime.datetime.fromtimestamp(revoke_time_stamp(timezone=config.config_object.TIMEZONE))
            time_expiry = datetime.datetime.fromtimestamp(payload["exp"])
            rd = dateutil.relativedelta.relativedelta (time_expiry, time_now)

            logger.warning("Difference between now and expiry of id_token")
            logger.warning(f"{rd.years} years, {rd.months} months, {rd.days} days, {rd.hours} hours, {rd.minutes} minutes and {rd.seconds} seconds")

            if rd.minutes < 20:
                logger.error("Renewing id_token, as it will expire soon")
                id_token = update_tokens(config.config_object, username, refresh_token)
          
            if isinstance(id_token, bytes):
                id_token = id_token.decode()

            response = await f(request, config.config_object, id_token, username, *args, **kwargs)
            return response
          
        return decorated_function
    return decorator









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
async def aws_creds(request, config, id_token, username):
    identity_id, access_key, secret_key, session_token =  await aws_temp_creds(config, id_token, username)
    async for msg in S3Backup.sync_backup(request.app.config, identity_id, access_key, secret_key, session_token):
        logger.info(msg)
    return response.json({"error": False, "sucess": True})

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
            logger.info(msg)
            
        new_log_entry = request.app.config.LOGS_TBL.create(timestamp=archival_object, message=f"Archival was successful on {archival_name}", error=0, success=1)
        new_log_entry.save()

    except Exception as e:
        logger.error(e.__str__())
        new_log_entry = request.app.config.LOGS_TBL.create(timestamp=archival_object, message=f"Archival failed because of {e.__str__()} on {archival_name}", error=1, success=0)
        new_log_entry.save()


    return response.json(
        {
        'error': False,
        'success': True,
        })