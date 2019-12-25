from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
import datetime
import humanize
from .utils import Backup, S3Backup
from loguru import logger
from .db_calls import get_stats, get_status,  delete_status, update_status, get_credentials, \
                update_mnemonic_n_address, insert_backup_entry, get_backup_list

from EncryptionModule.gen_mnemonic import generate_entropy, generate_mnemonic, child_keys 

from ..shared.utils import  creation_date, modification_date

import datetime
import dateutil
import hashlib
import requests
import json
import aiomisc
from .variables import DATASOURCE_NAME

##this is to import USERS variables name 
from ..datapod_users.variables import DATASOURCE_NAME as USER_DATASOURCE_NAME

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


    instance = await S3Backup(request.app.config)
    result = await instance.get_size(request.app.config.AWS_S3['bucket_name'])

    return response.json({
            "error": False,
            "success": True, 
            "data": result,
            "message": None
        })







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


async def temp_credentials(request):
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """
    creds = await get_credentials(request.app.config[USER_DATASOURCE_NAME]["tables"]["creds_table"])


    if not creds:
        raise APIBadRequest("User is not logged in")
    
    creds = list(creds)[0]
    r = requests.post(request.app.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
   
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    
    logger.debug(result)
    r = requests.post(request.app.config.TEMPORARY_S3_CREDS, data=json.dumps({"id_token": result["data"]["id_token"]}), headers={"Authorization": result["data"]["id_token"]})

    result = r.json()
    logger.debug(result)
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json({
        'error': False,
        'success': True,
        "data": result["data"]
       })



@logger.catch
async def backup_upload(config, backup_type):
    ##Backup type 0 full, type 1 partial
    # Method to handle the new backup and sync with s3 
 
    #await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "PROGRESS",  dest_path, request.json["path"])
    # creds = await get_credentials(config[USER_DATASOURCE_NAME]["tables"]["creds_table"])
    # await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "backup", "PROGRESS")


    # if not creds:
    #     raise APIBadRequest("User is not logged in")
    
    # creds = list(creds)[0]
    # #r = requests.post(config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
   

    # ##renew tokens 
    # r = requests.post(config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
   
    # login_result = r.json()["data"]



    try:
        backup_instance = Backup(config)
        destination_path, folder_name = await backup_instance.make_backup()

        # logger.success("Backups has been created, Now trying to sync with s3")
        #instance = await S3Backup(config, backup_instance.num)
        # instance = await S3Backup(config, 10)
        # await instance.check_size()
        # size = await instance.sync_backup(destination_path, folder_name)
    except Exception as e:
        logger.error(e)
        await insert_backup_entry(config[DATASOURCE_NAME]["tables"]["backup_list_table"], "fail", None, backup_type, None)
        await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "backup", "COMPLETED")    
        return 


    await insert_backup_entry(config[DATASOURCE_NAME]["tables"]["backup_list_table"], "success", size, backup_type, folder_name)
    await update_status(config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "backup", "COMPLETED")

    return 


async def login(config):

    creds = await get_credentials(config[USER_DATASOURCE_NAME]["tables"]["creds_table"])


    if not creds:
        raise APIBadRequest("User is not logged in")
    
    creds = list(creds)[0]
    #r = requests.post(request.app.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
   

    if creds["mnemonic"]:
        raise APIBadRequest("The mnemonic is already present")
    ##renew tokens 
    r = requests.post(config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
   
    login_result = r.json()
    return login_result["data"]



async def start_fresh_backup(request):
    """
    ##TODO ADD entries to BACKUP_TBL
    """
    ##This has a rare chance of happening, that users reach here and doesnt have mnemonic in the database but have mnemonic in the cloud
    await update_status(request.app.config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME,  "backup", "PROGRESS")

    try:
            
        request.app.add_task(backup_upload(request.app.config, 0))

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



async def new_mnemonic(request):

    mnemonic =  generate_mnemonic(request.app.config.LANGUAGE)
    result = {}
    for (index, word) in enumerate(mnemonic.split(" ")):
        result.update({f"mnemonic_phrase_{index}": word})

    return response.json({
        "error": True, 
        "success": False,
        "message": None,
        "data": result
    })


async def check_mnemonic(request):
    """
    API to be used when user has reinstalled datapod
    since he/she already has menmonic intialized somewhere in the past ,
    this mnemonic has to be checked against the hash of the Mnemonic  
    """



    request.app.config.VALIDATE_FIELDS(["mnemonic"], request.json)



    creds = await get_credentials(request.app.config[USER_DATASOURCE_NAME]["tables"]["creds_table"])

    if not creds:
        raise APIBadRequest("User is not logged in")
    
    creds = list(creds)[0]
    r = requests.post(request.app.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
   
    login_result = r.json()["data"]

    ##converting mnemonic list of words into a string of 24 words of mnemonic
    mnemonic = " ".join(request.json["mnemonic"])

    logger.debug(f"The mnemonic is {mnemonic}")
    sha3_256=hashlib.sha3_256(mnemonic.encode()).hexdigest()

    logger.debug(f"Sha 256 of mnemonic is {sha3_256}")
    r = requests.post(request.app.config.CHECK_MNEMONIC, data=json.dumps({
                "username":login_result["username"], 
                "sha3_256": sha3_256,
                }), headers={"Authorization": login_result["id_token"]})

    check_mnemonic_result = r.json()

    if check_mnemonic_result["error"]:
        raise APIBadRequest(check_mnemonic_result["message"])

    ##TODO Store mnemonic in the local db
    mnemonic_keys = child_keys(mnemonic, 0)
    await update_mnemonic_n_address(request.app.config[USER_DATASOURCE_NAME]["tables"]["creds_table"], 
                login_result["username"], 
                mnemonic, 
                mnemonic_keys["address"],   mnemonic_keys["private_key"])

    return response.json({
        "error": True, 
        "success": False,
        "message": "Mnemonic has been saved on your machine",
        "data": None
    })

async def store_mnemonic(request):
    """
    When the user is trying to access the feature of backup, 
    THe user has to finalize a mnemonic, whose hash will then be upload 
    on the remote API, 

    The password hash must be checked with the one stored in the credential tbl

    Simulateneously, A scrypt password will be genrated from the user password and 
    will be used to encrypt the user mnemonic
    """

    request.app.config.VALIDATE_FIELDS(["mnemonic"], request.json)

    mnemonic: list = request.json["mnemonic"]
    logger.info(f"This is the mnemonic {mnemonic}")
    if len(list(filter(None, mnemonic))) != 24:
        raise APIBadRequest("Please enter a mnemonic of length 24, Invalid Mnemonic")


    login_result = await login(request.app.config)



    mnemonic = " ".join(mnemonic)
    logger.info(f"Mnemonic as a list {mnemonic}")


    ##this will return  {"private_key", "public_key", "address"
    mnemonic_keys = child_keys(mnemonic, 0)
    logger.info(mnemonic_keys)

    ##check mnemonic hash stored against user on the dynamodb
    sha3_256=hashlib.sha3_256(mnemonic.encode()).hexdigest()




    r = requests.post(request.app.config.GET_USER, data=json.dumps({
                "username":login_result["username"], 
                }), headers={"Authorization": login_result["id_token"]})

    get_user_result = r.json()
    logger.debug(f"Get user result {get_user_result}")
    if get_user_result["error"]:
        raise APIBadRequest("This user doesnt exists")


    if get_user_result["data"].get("sha3_256"):
        raise APIBadRequest("The Mnemonic is already present for this user")




    ##Encrypting user mnemonic with the scrypt key generated from the users password
    # hex_salt, encrypted_mnemonic = encrypt_mnemonic(request.json["password"], mnemonic)

    # logger.info(f"Hex salt for Mnemonic Encryption {hex_salt}")
    # logger.info(f"Encrypted Mnemonic {encrypted_mnemonic}")
    sha3_512 = hashlib.sha3_512(mnemonic.encode()).hexdigest()
    logger.info(f"mnemonic_sha3_512 {sha3_512}")

    
    # logger.info("Saving user mnemonic hash on the dynamodb")

    ##updateing user details on the remote api with mnemonic sha3_256 and sha3_512 hash
    r = requests.post(request.app.config.UPDATE_MNEOMONIC, data=json.dumps({
                "public_key": mnemonic_keys["public_key"], 
                "username": login_result["username"], 
                "sha3_256": sha3_256,
                "sha3_512": sha3_512,
                "address": mnemonic_keys["address"]
                }), headers={"Authorization": login_result["id_token"]})

    update_result = r.json()
    logger.info(update_result)
    logger.info(r.status_code)


    if update_result.get("error"):
        logger.error(update_result["message"])
        raise APIBadRequest(update_result["message"])


    await update_mnemonic_n_address(request.app.config[USER_DATASOURCE_NAME]["tables"]["creds_table"], 
                login_result["username"], 
                mnemonic, 
                mnemonic_keys["address"],   mnemonic_keys["private_key"])

    ##UPDATE the local datasource status table,
    ##with a flag that SETUP_COMPLETED for the backup
    # update_datasources_status(request.app.config.DATASOURCES_TBL , "BACKUP", "backup" , request.app.config.DATASOURCES_CODE["BACKUP"], "Setup completed for backup", "SETUP_COMPLETED")

    return response.json({
        "error": True, 
        "success": False,
        "message": "Mnemonic has been saved and updated",
        "data": None
    })

