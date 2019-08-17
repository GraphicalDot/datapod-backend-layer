import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os

import json
from errors_module.errors import APIBadRequest
from database_calls.coderepos.github.calls import filter_repos, get_single_repository, filter_starred_repos, filter_gists
from loguru import logger
from .utils import construct_request, get_response, ensure_directory, \
        c_pretty_print, mask_password, logging_subprocess,  GithubIdentity,\
             retrieve_data, retrieve_data_gen, get_authenticated_user

from .backup_new import retrieve_repositories, backup_repositories, per_repository

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
    await backup_repositories(username, password, backup_path, repositories, config)
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



@GITHUB_BP.get('/list_repos')
async def listrepos(request):
    """
    """
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 10][request.args.get("number") == None] 

    result = await filter_repos(request.app.config.CODE_GITHUB_TBL, int(page), int(number))

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })


@GITHUB_BP.get('/list_starred_repos')
async def list_starred_repos(request):
    """
    """
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 10][request.args.get("number") == None] 

    result = await filter_starred_repos(request.app.config.CODE_GITHUB_TBL, int(page), int(number))

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })

@GITHUB_BP.get('/list_gists')
async def list_gist(request):
    """
    """
    logger.info("Number is ", request.args.get("number"))
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 10][request.args.get("number") == None] 

    result = await filter_gists(request.app.config.CODE_GITHUB_TBL, int(page), int(number))

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })


@GITHUB_BP.get('/get_repo')
async def listrepos(request):
    """
    """
    if not request.args.get("name"):
        raise APIBadRequest("Name of the repository is required")
    
    result = await get_single_repository(request.app.config.CODE_GITHUB_TBL, request.args.get("name"))
    if result:
        result = result[0]
        logger.info(result)
        owner = json.loads(result["owner"])
        result.update({"owner": owner})

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })




@GITHUB_BP.get('/backup_single_repo')
async def backup_single_repo(request):
    """
    """
    if not request.args.get("name"):
        raise APIBadRequest("Name of the repository is required")
    
    logger.info(request.app.config.CODE_GITHUB_TBL)

    result = await get_single_repository(request.app.config.CODE_GITHUB_TBL, request.args.get("name"))
    if not result:
        raise APIBadRequest("No repo exists")
    
    if result:
        repository = result[0]
        logger.info(repository)
        owner = json.loads(repository["owner"])
        repository.update({"owner": owner})    
        per_repository(repository["path"], repository, request.app.config.CODE_GITHUB_TBL, None)

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })



