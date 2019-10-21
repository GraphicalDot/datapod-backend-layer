


#-*- coding: utf-8 -*-
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3

from .db_initialize import initialize
from .github_api import github_parse, github_re_backup_whole, github_list_repos, github_identity, github_list_starred_repos, github_list_gist, \
        github_list_repos, github_backup_single_repo, stats, status

from .api import get_suggestions, codesearch
import os
from .variables import DATASOURCE_NAME



class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)

        creds_table, status_table, stats_table, archives_table, repos_table = initialize(self.db_object)                  
        self.datasource_name = DATASOURCE_NAME

        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
                "stats_table": stats_table, 
                "status_table": status_table,
                "archives_table": archives_table,
                "repos_table": repos_table},
            "utils":{
                "stats": stats, 
                "status": status
            }
        }
        
        self.routes = {"GET": [
                                    ("github/re_backup_whole", github_re_backup_whole), 
                                    ("github/list_repos", github_list_repos), 
                                    ("github/backup_single_repo", github_backup_single_repo), 
                                    ("github/list_starred_repos", github_list_starred_repos), 
                                    ("github/list_gists", github_list_gist), 
                                    ("github/github_list_repos", github_list_repos), 
                                    ("get_suggestions", get_suggestions),
                                    ("codesearch", codesearch)
                        ], 
                    "POST": [("github/parse", github_parse)] } 