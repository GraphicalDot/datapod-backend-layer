#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import aiomisc

#@retry(stop=stop_after_attempt(2))
@aiomisc.threaded
def update_status(status_table, datasource_name, username, status):
    try:
        status_table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        status_table.update(
            status=status).\
        where(status_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 

@aiomisc.threaded
def get_creds(credential_table, username):
    logger.info("Get credentials called")
    return credential_table.select().where(credential_table.username == username).dicts()

@aiomisc.threaded
def update_stats(stats_table, reposource, username, data_items, size, sync_frequency, sync_type, next_sync):
    """

    """
    try:
        stats_table.insert(
                source = reposource,
                username = username,
                data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).execute()
                                    
    except IntegrityError as e:
        logger.error(f"Couldnt insert stats for  because of {e} so updating it")

        stats_table.update(
                            data_items = data_items,
                disk_space_used = size).\
        where(stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {reposource} updated because of {e}")
    return 



@aiomisc.threaded
def get_status(status_table):
    return status_table.select().dicts()



@aiomisc.threaded
def get_stats(stats_table):
    return stats_table.select().dicts()



@aiomisc.threaded
def store_creds(tbl_object, username, password, reposource):
    """
    purchases: a list of purchases dict
    """


    try:
        tbl_object.insert(
                    username = username,
                    source = reposource,
                    password=password).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
        logger.success(f"Success on insert {reposource} creds for --{username}--")
        
    except IntegrityError as e:

        tbl_object.update(
                    password=password).where(tbl_object.username==username).execute()
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Github creds data insertion failed so updating it  {username}")

    except Exception as e:
        logger.error(f"Github creds data insertion failed {username} with error {e}")

    return 

@aiomisc.threaded
def get_creds(tbl_object):
        res = tbl_object.get_by_id(1)
        return res.username, res.password

@aiomisc.threaded
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
                    username = data["username"],
                    source=data["reposource"],
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
                    downloaded_at=datetime.datetime.now(),
                    is_starred=data.get("is_starred"),
                    is_gist=data.get("is_gist"),
                    default_branch=data.get("default_branch")).execute()

        logger.success(f"Success on insert github repo --{data['path']}-- username --{data['username']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        downloaded_at = datetime.datetime.now()

        logger.info(f'Updating --{data.get("name")}-- in table --GithubRepo-- with downloaded time {downloaded_at} ')

        

        table.update(
                    name = data.get("name"),
                    username = data["username"],
                    source=data["reposource"],
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
                    downloaded_at=downloaded_at,
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
        logger.success(f'Success in Updating --{data.get("username")}-- in table --GithubRepo-- ')

        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Github repo data insertion failed {data.get('name')} with {e}")
    return 





@aiomisc.threaded
def filter_repos(tbl_object, username, skip, limit, search_text):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """

    if search_text:

        query=  tbl_object\
                .select(tbl_object.name, tbl_object.git_url, 
                        tbl_object.source,
                        tbl_object.downloaded_at, 
                        tbl_object.id, 
                        tbl_object.node_id, 
                        tbl_object.created_at, 
                        tbl_object.updated_at, 
                        tbl_object.pushed_at,
                        tbl_object.description)\
                .where(tbl_object.username ==username, tbl_object.is_gist != True, tbl_object.is_starred != True, tbl_object.name**f'%{search_text}%')\
                .order_by(-tbl_object.updated_at)\
        
    else:
        query= tbl_object\
                .select(tbl_object.name, tbl_object.git_url, 
                        tbl_object.source,
                        tbl_object.downloaded_at, 
                        tbl_object.id, 
                        tbl_object.node_id, 
                        tbl_object.created_at, 
                        tbl_object.updated_at, 
                        tbl_object.pushed_at,
                        tbl_object.description)\
                .where(tbl_object.username ==username, tbl_object.is_gist != True, tbl_object.is_starred != True)\
                .order_by(-tbl_object.updated_at)\
        
  

    return  query.offset(skip).limit(limit).dicts(), query.count()




@aiomisc.threaded
def filter_starred_repos(tbl_object, username, skip, limit, search_text):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """


    if search_text:

        query=  tbl_object\
                .select(tbl_object.name, tbl_object.git_url, 
                        tbl_object.source,
                        tbl_object.downloaded_at, 
                        tbl_object.id, 
                        tbl_object.node_id, 
                        tbl_object.created_at, 
                        tbl_object.updated_at, 
                        tbl_object.pushed_at,
                        tbl_object.description)\
                .where(tbl_object.username ==username,
                         tbl_object.is_starred==True, 
                         tbl_object.name**f'%{search_text}%'| tbl_object.description**f'%{search_text}%'
                         )\
                .order_by(-tbl_object.updated_at)\
        
    else:
        query= tbl_object\
                .select(tbl_object.name, tbl_object.git_url, 
                        tbl_object.source,
                        tbl_object.downloaded_at, 
                        tbl_object.id, 
                        tbl_object.node_id, 
                        tbl_object.created_at, 
                        tbl_object.updated_at, 
                        tbl_object.pushed_at,
                        tbl_object.description)\
                .where(tbl_object.username ==username, tbl_object.is_starred==True)\
                .order_by(-tbl_object.updated_at)\
        
  

    return  query.offset(skip).limit(limit).dicts(), query.count()

@aiomisc.threaded
def filter_gists(tbl_object, username, skip, limit, search_text):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """


    if search_text:

        query=  tbl_object\
                .select(tbl_object.name, tbl_object.git_url, 
                        tbl_object.source,
                        tbl_object.downloaded_at, 
                        tbl_object.id, 
                        tbl_object.node_id, 
                        tbl_object.created_at, 
                        tbl_object.updated_at, 
                        tbl_object.pushed_at,
                        tbl_object.description)\
                .where(tbl_object.username ==username, tbl_object.is_gist==True, tbl_object.name**f'%{search_text}%')\
                .order_by(-tbl_object.updated_at)\
        
    else:
        query= tbl_object\
                .select(tbl_object.name, tbl_object.git_url, 
                        tbl_object.source,
                        tbl_object.downloaded_at, 
                        tbl_object.id, 
                        tbl_object.node_id, 
                        tbl_object.created_at, 
                        tbl_object.updated_at, 
                        tbl_object.pushed_at,
                        tbl_object.description)\
                .where(tbl_object.username ==username, tbl_object.is_gist==True)\
                .order_by(-tbl_object.updated_at)\
        
  

    return  query.offset(skip).limit(limit).dicts(), query.count()

# @aiomisc.threaded
# def filter_gists(tbl_object, username, page, number):
#     """
#         for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
#          print(tweet.message, tweet.created_date)

#     """
#     logger.info("Filter_gists has been caled")
#     return tbl_object\
#             .select(tbl_object.name, tbl_object.git_pull_url,
#              tbl_object.source, 
#                     tbl_object.downloaded_at, 
#                     tbl_object.id, 
#                     tbl_object.node_id, 
#                     tbl_object.created_at, 
#                     tbl_object.updated_at, 
#                     tbl_object.pushed_at,
#                     tbl_object.description)\
#             .where(tbl_object.username ==username, tbl_object.is_gist==True)\
#             .order_by(-tbl_object.updated_at)\
#             .paginate(page, number)\
#              .dicts()




@aiomisc.threaded
def get_single_repository(tbl_object, username, name):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (tbl_object\
            .select()\
            .where(tbl_object.username ==username, tbl_object.name==name).dicts())
    return list(query)



@aiomisc.threaded
def counts(tbl_object, username):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    gists = tbl_object\
            .select()\
            .where(tbl_object.username ==username,tbl_object.is_gist==True).count()
    
    repos = tbl_object\
            .select()\
            .where(tbl_object.username ==username, tbl_object.is_gist != True, tbl_object.is_starred != True).count()

    starred = tbl_object\
            .select()\
            .where(tbl_object.username ==username, tbl_object.is_starred==True).count()



    return {
        "gists_count": gists,
        "starred_count": starred,
        "repos_count": repos,
    }
