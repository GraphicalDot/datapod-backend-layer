

#-*- coding: utf-8 -*-
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3

from .db_initialize import initialize
from .api import parse, dashboard, tweets, allchats, stats, status
import os
from .variables import DATASOURCE_NAME



class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)


        creds_table, status_table, stats_table, archives_table,\
             account_table, tweet_table,\
             indexed_tweet_table = initialize(self.db_object)                  
        self.datasource_name = DATASOURCE_NAME

        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
                "archives_table": archives_table,
                "stats_table": stats_table, 
                "status_table": status_table, 
                "account_table": account_table,
                "tweet_table": tweet_table,
                "indexed_tweet_table": indexed_tweet_table},
            "utils":{
                "stats": stats, 
                "status": status
            }
        }
        
        self.routes = {"GET": [("dashboard", dashboard), ("tweets", tweets), 
                    ("chats", allchats)], 
                    "POST": [("parse", parse)] } 
        
        