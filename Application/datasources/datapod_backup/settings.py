
#-*- coding: utf-8 -*-
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3

from .db_initialize import initialize
from .api import  stats, status,  start_fresh_backup, new_mnemonic,\
         store_mnemonic, check_mnemonic, temp_credentials, backup_list
import os
from .variables import DATASOURCE_NAME



class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)

        backups_table, status_table, stats_table, backup_list_table =  initialize(self.db_object)
        self.datasource_name = DATASOURCE_NAME
        self.config  = { 
            "tables": { 
                "stats_table": stats_table, 
                "status_table": status_table,
                "backup_table": backups_table,
                "backup_list_table": backup_list_table,
            },
            "utils":{
                "stats": stats,
                "status": status
            }
        }
        
        self.routes = {"GET": [ ("stats", stats), ("status", status), ("backup_list", backup_list), ("temporary_credentials", temp_credentials),\
                    ("start_fresh_backup", start_fresh_backup),  ("generate_mnemonic", new_mnemonic)], 
                    "POST": [ ("store_mnemonic", store_mnemonic), ("check_mnemonic", check_mnemonic)]} 
        
        