

#-*- coding: utf-8 -*-
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3

from .db_initialize import initialize
from .api import parse, emails_filter,  reservations_filter,  image_filter,  attachment_filter,\
            stats, status, purchases_filter, locations_filter, delete_original_path, \
                cancel_parse, restart_parse
import os
from .variables import DATASOURCE_NAME



class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)


        creds_table, status_table, stats_table, email_table,\
             email_attachment_table, email_content_table,\
             image_table, purchase_table, reservation_table, \
                 archives_table, location_table, location_approximate_table = initialize(self.db_object)                  
        self.datasource_name = DATASOURCE_NAME

        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
                "image_table" : image_table,
                "email_table": email_table,
                "email_attachment_table": email_attachment_table,
                "email_content_table": email_content_table,
                "purchase_table": purchase_table,
                "archives_table": archives_table,
                "reservation_table": reservation_table,
                "location_table": location_table,
                "location_approximate_table": location_approximate_table,
                "stats_table": stats_table, 
                "status_table": status_table},
            "utils":{
                "stats": stats, 
                "status": status
            }
        }
        
        self.routes = {"GET": [("emails/filter", emails_filter), ("images/filter", image_filter), ("locations/filter", locations_filter), 
                    ("delete_zip", delete_original_path),
                    ("purchases/filter", purchases_filter), ("reservations/filter", reservations_filter), ("attachments/filter", attachment_filter)], 
                    "POST": [("parse", parse), ("cancel_parse", cancel_parse), ("restart_parse", restart_parse)] } 
        
        