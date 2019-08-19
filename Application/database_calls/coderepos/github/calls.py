#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from tenacity import *
from loguru import logger
from utils.utils import async_wrap

#@retry(stop=stop_after_attempt(2))
@async_wrap
def store(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    if not data.get("is_starred"):
        data["is_starred"] = False

    if not data.get("is_gist"):
        data["is_gist"] = False

    # if data.get("files"):
    #     data["files"] = json.dumps(data["files"])
    # else:
    #     data["files"] = None


    try:
        table.insert(
                    path = data["path"],
                    owner = json.dumps(data["owner"]),
                    id = str(data["id"]),
                    node_id = data["node_id"],
                    name = data.get("name"),
                    full_name = data.get("full_name"),
                    private = data.get("private"),
                    html_url = data.get("html_url"),
                    git_url = data.get("git_url"),
                    git_pull_url = data.get("git_pull_url"),
                    git_push_url = data.get("git_push_url"),
                    ssh_url = data.get("ssh_url"),
                    clone_url = data.get("clone_url"),
                    forks_url = data.get("forks_url"),
                    #files = data.get("files"), #only for gist
                    description = data.get("description"),
                    fork = data.get("fork"),
                    url = data.get("url"),
                    created_at = data.get("created_at"),
                    updated_at = data.get("updated_at"),
                    pushed_at = data.get("pushed_at"),
                    size = data.get("size"),
                    stargazers_count = data.get("stargazers_count"),
                    watchers_count = data.get("watchers_count"),
                    language = data.get("language"),
                    has_issues =  data.get("has_issues"),
                    has_projects  = data.get("has_projects"),
                    has_downloads = data.get("has_downloads"),
                    has_wiki=data.get("has_wiki"),
                    has_pages=data.get("has_pages"),
                    forks_count=data.get("forks_count"),
                    mirror_url= data.get("mirror_url"),
                    archived=data.get("archived"),
                    disabled= data.get("disabled"),
                    open_issues_count= data.get("open_issues_count"),
                    license=data.get("license"),
                    forks= data.get("forks"),
                    open_issues=data.get("open_issues"),
                    watchers=data.get("watchers"),
                    is_starred=data.get("is_starred"),
                    is_gist=data.get("is_gist"),
                    default_branch=data.get("default_branch")).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f'Duplicate key present --{data.get("name")}-- in table --GithubRepo-- {e}')
        logger.info(f'Updating --{data.get("name")}-- in table --GithubRepo-- ')



        table.update(
                    name = data.get("name"),
                    full_name = data.get("full_name"),
                    private = data.get("private"),
                    html_url = data.get("html_url"),
                    git_url = data.get("git_url"),
                    git_pull_url = data.get("git_pull_url"),
                    git_push_url = data.get("git_push_url"),
                    ssh_url = data.get("ssh_url"),
                    clone_url = data.get("clone_url"),
                    forks_url = data.get("forks_url"),
                    #files = data.get("files"), #only for gist
                    description = data.get("description"),
                    fork = data.get("fork"),
                    url = data.get("url"),
                    created_at = data.get("created_at"),
                    updated_at = data.get("updated_at"),
                    pushed_at = data.get("pushed_at"),
                    size = data.get("size"),
                    stargazers_count = data.get("stargazers_count"),
                    watchers_count = data.get("watchers_count"),
                    language = data.get("language"),
                    has_issues =  data.get("has_issues"),
                    has_projects  = data.get("has_projects"),
                    has_downloads = data.get("has_downloads"),
                    has_wiki=data.get("has_wiki"),
                    has_pages=data.get("has_pages"),
                    forks_count=data.get("forks_count"),
                    mirror_url= data.get("mirror_url"),
                    archived=data.get("archived"),
                    disabled= data.get("disabled"),
                    open_issues_count= data.get("open_issues_count"),
                    license=data.get("license"),
                    forks= data.get("forks"),
                    open_issues=data.get("open_issues"),
                    watchers=data.get("watchers"),
                    is_starred=data.get("is_starred"),
                    is_gist=data.get("is_gist"),
                    default_branch=data.get("default_branch"))\
                        .where(table.id==str(data["id"]))\
                        .execute()
        logger.success(f'Success in Updating --{data.get("name")}-- in table --GithubRepo-- ')

        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Github repo data insertion failed {data.get('name')} with {e}")
    return 


@async_wrap #makes function asynchronous
def filter_repos(tbl_object, page, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select(tbl_object.name, tbl_object.git_url, 
                    tbl_object.downloaded_at, 
                    tbl_object.id, 
                    tbl_object.node_id, 
                    tbl_object.created_at, 
                    tbl_object.updated_at, 
                    tbl_object.pushed_at,
                    tbl_object.description)\
            .where(tbl_object.is_gist != True, tbl_object.is_starred != True)\
            .order_by(-tbl_object.updated_at)\
            .paginate(page, number)\
             .dicts()

@async_wrap #makes function asynchronous
def filter_starred_repos(tbl_object, page, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select(tbl_object.name, tbl_object.git_url, 
                    tbl_object.downloaded_at, 
                    tbl_object.id, 
                    tbl_object.node_id, 
                    tbl_object.created_at, 
                    tbl_object.updated_at, 
                    tbl_object.pushed_at,
                    tbl_object.description)\
            .where(tbl_object.is_starred==True)\
            .order_by(-tbl_object.updated_at)\
            .paginate(page, number)\
             .dicts()



@async_wrap #makes function asynchronous
def filter_gists(tbl_object, page, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select(tbl_object.name, tbl_object.git_pull_url, 
                    tbl_object.downloaded_at, 
                    tbl_object.id, 
                    tbl_object.node_id, 
                    tbl_object.created_at, 
                    tbl_object.updated_at, 
                    tbl_object.pushed_at,
                    tbl_object.description)\
            .where(tbl_object.is_gist==True)\
            .order_by(-tbl_object.updated_at)\
            .paginate(page, number)\
             .dicts()




@async_wrap
def get_single_repository(tbl_object, name):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (tbl_object\
            .select()\
            .where(tbl_object.name==name).dicts())
    return list(query)



@async_wrap
def counts(tbl_object):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    gists = tbl_object\
            .select()\
            .where(tbl_object.is_gist==True).count()
    
    repos = tbl_object\
            .select()\
            .where(tbl_object.is_gist != True, tbl_object.is_starred != True).count()

    starred = tbl_object\
            .select()\
            .where(tbl_object.is_starred==True).count()



    return {
        "gists_count": gists,
        "starred_count": starred,
        "repos_count": repos,
    }
