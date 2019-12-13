
import requests
import json
import subprocess
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from errors_module.errors import APIBadRequest

from .db_calls import store_table_names, get_table_names, store_permission
from loguru import logger
import os
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3
from .db_initialize import initialize

DATASOURCE_NAME = "permissions"
from pathlib import Path 

pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]

db_path = os.path.dirname(os.path.abspath(__file__))

# db_path = os.path.join(db_path, f"{DATASOURCE_NAME}.db")


db_path = "~/.datapod/userdata/raw"

home = str(Path.home()) 


db_path = os.path.join(home, ".datapod/userdata/raw",   f"{DATASOURCE_NAME}.db")
logger.debug(f"Path for perimssion db is {db_path}")

# if not os.path.exists(db_path):
#     logger.debug("This path doesnt exists")
#     os.makedirs(db_path)

db_object = SqliteExtDatabase(db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)

permission_table, tables_name_table = initialize(db_object)


def store_tables(permissions_dict):
    """
    {'backup': ['stats_table', 'status_table', 'backup_table', 'backup_list_table'], 
    'coderepos': ['creds_table', 'stats_table', 'status_table', 'archives_table', 'repos_table'], 
    'facebook': ['creds_table', 'image_table', 'archives_table', 'yourposts_table', 'other_posts', 
            'content', 'chat_table', 'chat_content', 'stats_table', 'address_table', 'status_table'], 
    'google': ['creds_table', 'image_table', 'email_table', 'email_attachment_table', 'email_content_table', 
            'purchase_table', 'archives_table', 'reservation_table', 'location_table', 'location_approximate_table', 
            'stats_table', 'status_table'],
    'twitter': ['creds_table', 'archives_table', 'stats_table', 'status_table', 'account_table', 
                'tweet_table', 'indexed_tweet_table'], 'users': ['creds_table']}

    """

    for (key, value) in permissions_dict.items(): 
        for table_name in value:
            try:
                data = {"datasource_name": key, "table_name": table_name, 
                        "display_name" : table_name.replace("_table", "").replace("_", " ").capitalize(),
                        "tbl_object": tables_name_table} 
                store_table_names(**data)
            except Exception as e:
                logger.error(e)
                pass

    return




async def get_tables(request):
    """
    """

    data = await get_table_names(tables_name_table)

    return response.json({
        'error': False,
        'success': True,
        "message": None,
        "data": data})









async def store_permissions(request):
    """
    {'backup': ['stats_table', 'status_table', 'backup_table', 'backup_list_table'], 
    'coderepos': ['creds_table', 'stats_table', 'status_table', 'archives_table', 'repos_table'], 
    'facebook': ['creds_table', 'image_table', 'archives_table', 'yourposts_table', 'other_posts', 
            'content', 'chat_table', 'chat_content', 'stats_table', 'address_table', 'status_table'], 
    'google': ['creds_table', 'image_table', 'email_table', 'email_attachment_table', 'email_content_table', 
            'purchase_table', 'archives_table', 'reservation_table', 'location_table', 'location_approximate_table', 
            'stats_table', 'status_table'],
    'twitter': ['creds_table', 'archives_table', 'stats_table', 'status_table', 'account_table', 
                'tweet_table', 'indexed_tweet_table'], 'users': ['creds_table']}

    """

    request.app.config.VALIDATE_FIELDS(["plugin_name", "permissions"], request.json)

    logger.debug(request.json["permissions"])
    if not isinstance(request.json['permissions'], list):
        raise APIBadRequest("Permissions should be instance of list")


    if not request.json["plugin_name"]  in request.app.config.plugins:
        raise APIBadRequest("Plugin is unknown")


    for permission in request.json["permissions"]:
        permission.update({"tbl_object": permission_table, "plugin_name": request.json["plugin_name"] })
        await store_permission(**permission)

    return response.json({
        'error': False,
        'success': True,
        "message": None,
        "data": None})


