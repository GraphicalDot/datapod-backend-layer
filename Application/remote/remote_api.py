#-*- coding: utf-8 -*-

"""
This module deals with the only api's which will deal with the remote calls on our servers
registration and the upload of encrypted data dump
"""


import shutil
import time
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
from EncryptionModule.symmetric import aes_decrypt, aes_encrypt, generate_scrypt_key
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
REMOTE_BP = Blueprint("remote", url_prefix="/remote")


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise Exception("Improper JSON format")





@REMOTE_BP.post('/registration')
async def registration(request):
    """
    """
    required_fields = ["username", "password", "email"]
    validate_fields(required_fields, request.json)


    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
        })




@REMOTE_BP.post('/login')
async def login(request):
    """
    """
    required_fields = ["username", "password"]
    validate_fields(required_fields, request.json)


    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
        })



async def archive(source_destination_list):
    ##add this if this has to executed periodically
    ##while True:
    password = "BIGzoho8681@#"
    key, salt = generate_scrypt_key(password)
    logging.info(f"salt for scrypt key is {salt}")
    logging.info(f" key for AES encryption is  {key}")

    for (source, destination, encrypted_path) in source_destination_list: 
        shutil.make_archive(destination, 'zip', source)
        logger.info(f"Archiving done at the path {destination}")
        time.sleep(1)
        with open("%s.zip"%destination, "rb") as f:
            file_bytes = f.read()
            data = aes_encrypt(key, file_bytes)
            with open(encrypted_path, "wb") as f:
                f.write(data)


    return 


@REMOTE_BP.post('/upload_dump')
async def upload_dump(request):
    """
    """
    required_fields = ["token"]
    validate_fields(required_fields, request.json)

    user_archive = os.path.join(request.app.config.archive_path, "user_data.data")
    encrypted_user_archive = os.path.join(request.app.config.archive_path, "user_data.encrypt")

    db_archive = os.path.join(request.app.config.archive_path, "database.data")
    encrypted_db_archive = os.path.join(request.app.config.archive_path, "database.encrypt")

    #shutil.make_archive(user_archive, 'zip', request.app.config.user_data_path)
    #shutil.make_archive(db_archive, 'zip', request.app.config.db_dir_path)

    request.app.add_task(archive([   
            (request.app.config.user_data_path, user_archive, encrypted_db_archive), 
            (request.app.config.db_dir_path, db_archive, encrypted_user_archive)
    ]))

    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Dude some empty data"
        })


