

#-*- coding: utf-8 -*-
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3

from .db_initialize import initialize
from .api import login, signup, confirm_signup, change_password, forgot_password,\
             confirm_forgot_password, is_logged_in, user_logout, temp_credentials
import os
from .variables import DATASOURCE_NAME



class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)

        creds_table =  initialize(self.db_object)
        self.datasource_name = DATASOURCE_NAME
        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
              },
            "utils":{
            }
        }
        
        self.routes = {"GET": [ ("logout", user_logout),("is_logged_in", is_logged_in), ("temporary_credentials", temp_credentials)], 
                    "POST": [("login", login), 
                            ("signup", signup),
                            ("confirm_signup", confirm_signup), 
                            ("forgot_password", forgot_password),
                            ("confirm_forgot_password", confirm_forgot_password),
                            ("change_password", change_password)] } 
        
        