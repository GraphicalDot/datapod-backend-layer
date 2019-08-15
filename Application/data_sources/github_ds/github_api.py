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
from loguru import logger
from .utils import construct_request, get_response, ensure_directory, \
        c_pretty_print, mask_password, logging_subprocess,  GithubIdentity,\
             retrieve_data, retrieve_data_gen

GITHUB_BP = Blueprint("github", url_prefix="/github")


async def background_github_parse(config, username, password):
    
    try:
        inst = GithubIdentity("github.com", "datapod")
        inst.add(username, password)

    except Exception as e:
       logger.error(e)

    
    #generate_new_keys(username, password)
    # dirname = os.path.dirname(os.path.abspath(__file__))
    # output_directory = os.path.join(dirname, "account") 
    # if args.lfs_clone:
    #     check_git_lfs_install()
    # logger.info('Backing up user {0} to {1}'.format(username, config_object.GITHUB_OUTPUT_DIR))

    # ensure_directory(config_object.GITHUB_OUTPUT_DIR)

    # authenticated_user = get_authenticated_user(username, password)

    # logger.info(f"The user for which the backup will happend {authenticated_user['login']}")
    # repositories = retrieve_repositories(username, password)
    # #repositories = filter_repositories(args, repositories)
    # backup_repositories(username, password, config_object.GITHUB_OUTPUT_DIR, repositories)
    # # backup_account(args, output_directory)


@GITHUB_BP.post('/parse')
async def parse(request):
    """
    """

    request.app.config.VALIDATE_FIELDS(["username", "password"], request.json)
    try:
        inst = GithubIdentity(request.app.config, "github.com", "datapod")
        await inst.add(request.json["username"], request.json["password"])

    except Exception as e:
       logger.error(e)
       raise APIBadRequest(e)




    # else:
    #     raise APIBadRequest("Unknown format")

    # logger.info(f"THe request was successful with github path {request.json['path']}")
    # request.app.add_task(backup_upload(request.app.config, request["user_data"]["id_token"]))

    return response.json(
        {
        'error': False,
        'success': True,
        })









