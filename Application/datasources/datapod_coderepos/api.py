from sanic.request import RequestParameters
from sanic import response
import os
import subprocess
import json
from dateutil.parser import parse as date_parse 
from .utils.github_auth import get_auth
from errors_module.errors import APIBadRequest

from loguru import logger
import aiomisc
import mmap
import humanize
import csv




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


@aiomisc.threaded_separate
def search_text(command): 
    # try: 
    #     with open(filepath, 'rb', 0) as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s: 
    #         if s.find(string.encode()) != -1: 
    #             return True 
    # except: 
    #     return False 
    # process = subprocess.Popen(command, stdout=subprocess.PIPE)
    # stdout, _ = process.communicate()

    # reader = csv.DictReader(stdout.decode('ascii').splitlines(),
    #                     delimiter=' ', skipinitialspace=True,
    #                     fieldnames=['filename', 'line_number',
    #                                 'text'])

    result = []



    result = subprocess.getoutput(command)
    result = result.split("\n")
    return result

async def codesearch(request):

    raw_text = request.args.get("search_text")

    skip = [request.args.get("skip"), 0][request.args.get("skip") == None] 
    limit = [request.args.get("limit"), 20][request.args.get("limit") == None] 


    if not raw_text:
        raise APIBadRequest("Raw text  which is to be searched is required")

    path = os.path.join(request.app.config.RAW_DATA_PATH, "Coderepos/github")
    
    grep_command = f"grep -InrH {raw_text} {path}/*"
    # grep_command = ["grep", "-InrH", raw_text, path]
    logger.info(grep_command)
    result = await search_text(grep_command)
    logger.info(result)
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
        'data': result, 
        'message': None
        })