import shutil
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import subprocess
import datetime
import humanize
import json
from dateutil.parser import parse as date_parse 
from .utils.github_auth import get_auth
from .errors.errors import APIBadRequest, IdentityAlreadyExists,  IdentityExistsNoPath, IdentityDoesntExists
from .db_calls import filter_repos, get_single_repository, filter_starred_repos, filter_gists, counts, store_creds, get_creds, update_status, update_stats

from loguru import logger
from .utils.common import construct_request, get_response, ensure_directory, \
        c_pretty_print, mask_password, logging_subprocess, \
             retrieve_data, retrieve_data_gen, get_authenticated_user
from .utils.github_identity import GithubIdentity

import mmap
import humanize
import aiomisc

from .utils.github_backup import retrieve_repositories, backup_repositories, per_repository
#from gitsuggest import GitSuggest
from github import Github , BadCredentialsException, GithubException



async def stats(request):
    
    def get_dir_size(dirpath):
        subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')


    datasource_dir = os.path.join(request.app.config["RAW_DATA_PATH"], DATASOURCE_NAME)
    usernames = [{"username": x[0], "path": os.path.join(datasource_dir, x[0])} for x in os.walk(datasource_dir)]

    for username in usernames:
        size = get_dir_size(username["path"])


    pass


async def status(request):
    res = await get_datasources_status(update_datasources_status(config[datasource_name]["tables"]["status"]))
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": None, 
        "data": res
        })



async def background_github_parse(config, username, password, re_backup=False):
    backup_path = os.path.join(config.RAW_DATA_PATH, "Coderepos/github")
    ensure_directory(backup_path)

    authenticated_user = get_authenticated_user(username, password)

    repositories = retrieve_repositories(username, password)
    #repositories = filter_repositories(args, repositories)
    await backup_repositories(username, password, backup_path, repositories, config, re_backup)
    # # backup_account(args, output_directory)


    ##after completeion og the github parse, update the datasources table with the COMPLETED status
    if not re_backup:
        update_datasources_status(config.DATASOURCES_TBL , "CODEREPOS/Github", username , config.DATASOURCES_CODE["REPOSITORY"]["GITHUB"], "COMPLETED", "COMPLETED")


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




def deactivate():
    """
    This method is required to deactivate Github from Datapod
    First remove the keys registry from ~/.ssh/config file  
    """
    ##somwhow remove hostname github in config in .ssh
    ##delete the datapod key of the rmeote Code Repo like github

    return 

async def github_parse(request):
    """
    """

    request.app.config.VALIDATE_FIELDS(["username", "password"], request.json)


    try:
        logger.info(f'Github username {request.json["username"]}')

        logger.info(f'Github username {request.json["password"]}')

        g = Github(request.json["username"], request.json["password"] ) 
        g.get_user().disk_usage 
    except BadCredentialsException:
        raise APIBadRequest("User credentials are incorrect")
    except Exception as e:
        raise APIBadRequest(e)

    try:
        inst = await GithubIdentity(request.app.config, "github.com", "datapod", request.json["username"], request.json["password"])
        await inst.keys_path()



    except IdentityAlreadyExists as e:
        logger.warning(f"GithubDS Error {e}")

    except IdentityDoesntExists as e:
        logger.info(f"Github Keys doesnt exists creating one")
        await inst.add()

    except IdentityExistsNoPath as e:
        ##this implies host is present in config but path of privatekey doesnt exists
        logger.warning(f"Github Warning {e}")
        await inst.update()

    except Exception as e :
        ##this implies host is present in config but path of privatekey doesnt exists
        logger.error(f"GithubDS Error {e}")
        raise APIBadRequest(e)

    await store_creds(request.app.config.CODE_GITHUB_CREDS_TBL, request.json["username"], request.json["password"] )
    update_datasources_status(request.app.config.DATASOURCES_TBL , "CODEREPOS/Github",request.json["username"] , \
            request.app.config.DATASOURCES_CODE["REPOSITORY"]["GITHUB"], "github parse completed", "PROGRESS")


    request.app.add_task(background_github_parse(request.app.config, request.json["username"], request.json["password"]))

    return response.json(
        {
        'error': False,
        'success': True,
        })



async def github_re_backup_whole(request):
    """
    """

    try:
        username, password = await get_creds(request.app.config.CODE_GITHUB_CREDS_TBL)
    except:
        raise APIBadRequest("Credentials aren't present")
    

    #update_datasources_status(request.app.config.DATASOURCES_TBL , "CODEREPOS/Github",request.json["username"] , request.app.config.DATASOURCES_CODE["REPOSITORY"]["GITHUB"], "IN_PROGRESS", "PROGRESS")

    # else:
    #     raise APIBadRequest("Unknown format")

    # logger.info(f"THe request was successful with github path {request.json['path']}")
    request.app.add_task(background_github_parse(request.app.config, username, password, re_backup=True))

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Your whole github backup has started, Once done it will start reflecting on your github Dashboard",
        "data": None, 
        })




async def github_list_repos(request):
    """
    """
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 200][request.args.get("number") == None] 

    result = await filter_repos(request.app.config.CODE_GITHUB_TBL, int(page), int(number))
    [repo.update({
            "downloaded_at": repo.get("downloaded_at").strftime("%d, %b %Y"),
            "created_at": date_parse( repo.get("created_at")).strftime("%d, %b %Y"),
            "updated_at": date_parse( repo.get("updated_at")).strftime("%d, %b %Y"),
            "pushed_at": date_parse( repo.get("pushed_at")).strftime("%d, %b %Y")
    }) for repo in result]
    
    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })



async def github_identity(request):
    """
    """
    identity, ssh_dir = GithubIdentity.identity_exist("github.com")
    logger.info(f"The ssh Directory is {ssh_dir}")

    private_key_path = os.path.join(ssh_dir, "git_priv.key")
    public_key_path = os.path.join(ssh_dir, "git_pub.key")


    if not private_key_path and not public_key_path:
        raise APIBadRequest("Identity doesnt not exists")

    return response.json(
        {
        'error': False,
        'success': True,
        'data': identity,
        'message': None
        })



async def github_list_starred_repos(request):
    """
    """
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 200][request.args.get("number") == None] 

    result = await filter_starred_repos(request.app.config.CODE_GITHUB_TBL, int(page), int(number))
    for repo in result:
        try:
            repo.update({
                        "downloaded_at": repo.get("downloaded_at").strftime("%d, %b %Y"),
                        "created_at": date_parse( repo.get("created_at")).strftime("%d, %b %Y"),
                        "updated_at": date_parse( repo.get("updated_at")).strftime("%d, %b %Y"),
                        "pushed_at": date_parse( repo.get("pushed_at")).strftime("%d, %b %Y")
                })
        except :
            logger.error(repo)
            pass

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })

async def github_list_gist(request):
    """
    """
    logger.info("Number is ", request.args.get("number"))
    page = [request.args.get("page"), 1][request.args.get("page") == None] 
    number = [request.args.get("number"), 200][request.args.get("number") == None] 

    result = await filter_gists(request.app.config.CODE_GITHUB_TBL, int(page), int(number))
    [repo.update({
            "downloaded_at": repo.get("downloaded_at").strftime("%d, %b %Y"),
            "created_at": date_parse( repo.get("created_at")).strftime("%d, %b %Y"),
            "updated_at": date_parse( repo.get("updated_at")).strftime("%d, %b %Y")
        }) for repo in result]

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })


async def github_list_repos(request):
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


async def github_backup_single_repo(request):
    """
    """
    if not request.args.get("name"):
        raise APIBadRequest("Name of the repository is required")
    
    logger.info(request.app.config.CODE_GITHUB_TBL)

    result = await get_single_repository(request.app.config.CODE_GITHUB_TBL, request.args.get("name"))
    
    if not result:
        raise APIBadRequest("No repo exists")
    
   
    for repository in  result:
        logger.info(repository)
        owner = json.loads(repository["owner"])
        repository.update({"owner": owner})    

        request.app.add_task(per_repository(repository["path"], repository, request.app.config, None))

    ##await per_repository(repository["path"], repository, request.app.config, None)

    return response.json(
        {
        'error': False,
        'success': True,
        'message': f"Backup the repository {request.args.get('name')} has been started",
        'data': None
        })

