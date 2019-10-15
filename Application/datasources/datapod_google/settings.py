

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
        
        self.db_path = os.path.join(db_path, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)


        creds_table, status_table, stats_table, email_table,\
             email_attachment_table, email_content_table,\
             image_table, purchase_table, reservation_table = initialize(self.db_object)                  
        self.datasource_name = DATASOURCE_NAME

        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
                "image_table" : image_table,
                "email_table": email_table,
                "email_attachment_table": email_attachment_table,
                "email_content_table": email_content_table,
                "purchase_table": purchase_table,
                "reservation_table": reservation_table,
                "stats_table": stats_table, 
                "status_table": status_table},
            "utils":{
                "stats": stats, 
                "status": status
            }
        }
        
        self.routes = {"GET": [("images", images), ("chats", allchats), ("stats", stats), ("status", status)], 
                    "POST": [("parse", parse)] } 
        
        