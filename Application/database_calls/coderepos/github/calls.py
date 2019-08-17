#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from tenacity import *
from loguru import logger


#@retry(stop=stop_after_attempt(2))
def store(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    if not data.get("is_starred"):
        data["is_starred"] = False

    if not data.get("is_gist"):
        data["is_gist"] = False
    try:
        table.insert(
                    path = data["path"],
                    owner = json.dumps(data["owner"]),
                    id = data["id"],
                    node_id = data["node_id"],
                    name = data["name"],
                    full_name = data["full_name"],
                    private = data["private"],
                    html_url = data["html_url"],
                    git_url = data["git_url"],
                    ssh_url = data["ssh_url"],
                    clone_url = data["clone_url"],
                    forks_url = data["forks_url"],

                    description = data["description"],
                    fork = data["fork"],
                    url = data["url"],
                    created_at = data["created_at"],
                    updated_at = data["updated_at"],
                    pushed_at = data["pushed_at"],
                    size = data["size"],
                    stargazers_count = data["stargazers_count"],
                    watchers_count = data["watchers_count"],
                    language = data["language"],
                    has_issues =  data["has_issues"],
                    has_projects  = data["has_projects"],
                    has_downloads = data["has_downloads"],
                    has_wiki=data["has_wiki"],
                    has_pages=data["has_pages"],
                    forks_count=data["forks_count"],
                    mirror_url= data["mirror_url"],
                    archived=data["archived"],
                    disabled= data["disabled"],
                    open_issues_count= data["open_issues_count"],
                    license=data["license"],
                    forks= data["forks"],
                    open_issues=data["open_issues"],
                    watchers=data["watchers"],
                    is_starred=data.get("is_starred"),
                    is_gist=data.get("is_gist"),
                    default_branch=data["default_branch"]).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f'Duplicate key present --{data["name"]}-- in table --GithubRepo-- {e}')
        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email data insertion failed {data['name']} with {e}")
    return 


def filter_repos(tbl_object, page, number):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    return tbl_object\
            .select(tbl_object.name, tbl_object.git_url, 
                    tbl_object.downloaded_at, 
                    tbl_object.created_at, 
                    tbl_object.updated_at, 
                    tbl_object.is_starred, 
                    tbl_object.pushed_at,
                    tbl_object.description)\
            .where(tbl_object.is_starred==False)\
            .order_by(-tbl_object.updated_at)\
            .paginate(page, number)\
             .dicts()
       
def get_single_repository(tbl_object, name):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (tbl_object\
            .select()\
            .where(tbl_object.name==name).dicts())
    return list(query)
