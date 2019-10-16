

#-*- coding: utf-8 -*-
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3

from .db_initialize import initialize
from .api import parse, images, allchats, stats, status 
import os
from .variables import DATASOURCE_NAME



class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)

        creds_table, archives_table, images_table, \
            yourposts_table,  other_posts, \
                content, status_table, stats_table =  initialize(self.db_object)
        self.datasource_name = DATASOURCE_NAME
        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
                "image_table" : images_table,
                "archives_table": archives_table,
                "yourposts_table": yourposts_table,
                "other_posts": other_posts,
                "content": content,
                "stats": stats_table, 
                "status": status_table},
            "utils":{
                "stats": stats, 
                "status": status
            }
        }
        
        self.routes = {"GET": [("images", images), ("chats", allchats), ("stats", stats), ("status", status)], 
                    "POST": [("parse", parse)] } 
        
        