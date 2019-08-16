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
from database_calls.coderepos.github.calls import filter_repos
from loguru import logger
from .utils import construct_request, get_response, ensure_directory, \
        c_pretty_print, mask_password, logging_subprocess,  GithubIdentity,\
             retrieve_data, retrieve_data_gen, get_authenticated_user

from .backup_new import retrieve_repositories, backup_repositories

GITHUB_BP = Blueprint("github", url_prefix="/github")


async def background_github_parse(config, username, password):
    logger.info("Background repositories backup started")
    backup_path = os.path.join(config.RAW_DATA_PATH, "Coderepos/github")
    logger.info(f"Path for backup of github repos is {backup_path}")
    ensure_directory(backup_path)

    authenticated_user = get_authenticated_user(username, password)

    logger.info(f"The user for which the backup will happend {authenticated_user['login']}")
    repositories = retrieve_repositories(username, password)
    logger.info("\nTHese are the repositories for the user\n")
    #repositories = filter_repositories(args, repositories)
    backup_repositories(username, password, backup_path, repositories, config.CODE_GITHUB_TBL)
    # # backup_account(args, output_directory)



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
        inst = await GithubIdentity(request.app.config, "github.com", "datapod")
        await inst.add(request.json["username"], request.json["password"])

    except Exception as e:
        logger.error(e)
        pass



    # else:
    #     raise APIBadRequest("Unknown format")

    # logger.info(f"THe request was successful with github path {request.json['path']}")
    request.app.add_task(background_github_parse(request.app.config, request.json["username"], request.json["password"]))

    return response.json(
        {
        'error': False,
        'success': True,
        })



@GITHUB_BP.get('/listrepos')
async def listrepos(request):
    """
    """
    logger.info("Number is ", request.args.get("number"))
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 10][request.args.get("number") == None] 

    result = filter_repos(request.app.config.CODE_GITHUB_TBL, int(page), int(number))

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })








