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
from .auth import get_auth
from errors_module.errors import APIBadRequest, IdentityAlreadyExists,  IdentityExistsNoPath, IdentityDoesntExists
from database_calls.coderepos.github.calls import filter_repos, get_single_repository, filter_starred_repos, filter_gists, counts, store_creds, get_creds
from database_calls.credentials import update_datasources_status, datasource_status

from loguru import logger
from .utils import construct_request, get_response, ensure_directory, \
        c_pretty_print, mask_password, logging_subprocess,  GithubIdentity,\
             retrieve_data, retrieve_data_gen, get_authenticated_user
import mmap
import humanize
from utils.utils import async_wrap

from utils.utils import creation_date
from .backup_new import retrieve_repositories, backup_repositories, per_repository
#from gitsuggest import GitSuggest

GITHUB_BP = Blueprint("github", url_prefix="/github")


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

@GITHUB_BP.post('/parse')
async def parse(request):
    """
    """

    request.app.config.VALIDATE_FIELDS(["username", "password"], request.json)
    try:
        inst = await GithubIdentity(request.app.config, "github.com", "datapod", request.json["username"], request.json["password"])
        await inst.keys_path()



    except IdentityAlreadyExists as e:
        logger.success(f"GithubDS Error {e}")

    except IdentityDoesntExists as e:
        await inst.add(request.json["username"], request.json["password"])
        logger.success(f"GithubDS Error {e}")

    except IdentityExistsNoPath as e:
        ##this implies host is present in config but path of privatekey doesnt exists
        logger.success(f"GithubDS Error {e}")
        await inst.update()

    await store_creds(request.app.config.CODE_GITHUB_CREDS_TBL, request.json["username"], request.json["password"] )
    update_datasources_status(request.app.config.DATASOURCES_TBL , "CODEREPOS/Github",request.json["username"] , \
            request.app.config.DATASOURCES_CODE["REPOSITORY"]["GITHUB"], "github parse completed", "PROGRESS")


    request.app.add_task(background_github_parse(request.app.config, request.json["username"], request.json["password"]))

    return response.json(
        {
        'error': False,
        'success': True,
        })



@GITHUB_BP.get('/re_backup_whole')
async def re_backup_whole(request):
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




@GITHUB_BP.get('/list_repos')
async def listrepos(request):
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



@GITHUB_BP.get('/identity')
async def listrepos(request):
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



@GITHUB_BP.get('/list_starred_repos')
async def list_starred_repos(request):
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

@GITHUB_BP.get('/list_gists')
async def list_gist(request):
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


@GITHUB_BP.get('/dashboard_data')
async def dashboard_data(request):
    """
    """
    result = await counts(request.app.config.CODE_GITHUB_TBL)
    starred = await filter_starred_repos(request.app.config.CODE_GITHUB_TBL, 1, 10)
    repos = await filter_repos(request.app.config.CODE_GITHUB_TBL, 1, 10)

    def get_dir_size(dirpath):
        all_files = [os.path.join(basedir, filename) for basedir, dirs, files in os.walk(dirpath) for filename in files]
        _date = creation_date(all_files[0])
        #files_and_sizes = [os.path.getsize(path) for path in all_files]
        return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8'), _date

    path = os.path.join(request.app.config.RAW_DATA_PATH, "Coderepos/github")
    size, last_updated = get_dir_size(path)

    result.update({"size": size, "last_updated": last_updated, "starred": starred, "repos": repos})

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



@GITHUB_BP.get('/parse_status')
async def parse_status(request):
    """
    """
    code = request.app.config.DATASOURCES_CODE["REPOSITORY"]["GITHUB"]
    result = datasource_status(request.app.config.DATASOURCES_TBL,code)
    logger.info(result)
    if result:
        result = result[0]
    else:
        result = {}

    return response.json(
        {
        'error': False,
        'success': True,
        'data': result,
        'message': None
        })

@GITHUB_BP.get('/get_suggestions')
async def get_suggestions(request):

    username, password = await get_creds(request.app.config.CODE_GITHUB_CREDS_TBL)
    
    deep_dive = request.args.get("deep_dive")
    logger.info(f"Deep dive is {deep_dive}")

    # To use with username password combination
    # if not deep_dive:
    #     gs = GitSuggest(username=username, password=password)
    # else:
    #     gs = GitSuggest(username=username, deep_dive=True)


    # To use with access_token
    #gs = GitSuggest(token="access_token")

    # To use without authenticating
    #gs = GitSuggest(username="<username>")

    # # To use with deep dive flag
    # gs = GitSuggest(username=<username>, password=<password>, token=None, deep_dive=True)
    # gs = GitSuggest(token=access_token, deep_dive=True)
    # gs = GitSuggest(username=<username>, deep_dive=True)

    # To get an iterator over suggested repositories.
    auth = get_auth(username, password, encode=True)
    logger.info(f"This is the auth {auth}")
    result = []
    for repo in gs.get_suggested_repositories():
        result.append({"name": repo.full_name, "description": repo.description, 
            "stars": repo.stargazers_count, "url": repo.git_url,  "updated_at": repo.updated_at.strftime("%d, %b %Y")})
    
    return response.json(
        {
        'error': False,
        'success': True,
        'result': result,
        'message': None
        })


@async_wrap
def search_text(filepath, string): 
    try: 
        with open(filepath, 'rb', 0) as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s: 
            if s.find(string.encode()) != -1: 
                return True 
    except: 
        return False 



@GITHUB_BP.get('/rawtext')
async def rawtext(request):

    raw_text = request.args.get("rawtext")
    if not raw_text:
        raise APIBadRequest("Raw text  which is to be searched is required")

    path = os.path.join(request.app.config.RAW_DATA_PATH, "Coderepos/github")
    
    grep_command = f"grep -nr {raw_text} {path}/*"

    result = []
    result = subprocess.getoutput(grep_command)
    result = result.split("\n")

    # for out in request.app.config.OS_COMMAND_OUTPUT(grep_command, "Files are in Sync"):
    #     logger.info(out)
    #     result.append(out)
    # # all_directories = [os.path.join(backup_path, dirname) for dirname in os.listdir(backup_path)]
    # all_file = lambda dirpath: [os.path.join(path, name) for path, subdirs, files in os.walk(dirpath) for name in files]

    # logger.info(all_directories)

    # allfiles =[]
    # for dirpath in all_directories:
    #     allfiles.extend(all_file(dirpath))


    # # result = []
    # # for filepath in allfiles: 
    # #     if await search_text(filepath, request.args.get("rawtext")): 
    # #         result.append(filepath)

    # tasks = [search_text(filepath, request.args.get("rawtext")) for filepath in allfiles]
    # result = await asyncio.gather(*tasks)
    
    #logger.info(f"Total number of files are {len(allfiles)}")
    return response.json(
        {
        'error': False,
        'success': True,
        'data': None, 
        'result': result
        })