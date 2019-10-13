

#-*- coding: utf-8 -*-

from .db_initialize import initialize
from .api import parse, images, allchats, stats, status, DATASOURCE_NAME 


class Routes:
    def __init__(self, db_object):
        self.db_object = db_object
        creds_table, archives_table, images_table, yourposts_table,  other_posts, content =  initialize(self.db_object)
        self.datasource_name = DATASOURCE_NAME
        self.config  = { "tables": { 
                "creds_table": creds_table,
                "image_table" : images_table,
                "archives_table": archives_table,
                "yourposts_table": yourposts_table,
                "other_posts": other_posts,
                "content": content}
        }
        
        self.routes = {"GET": [("images", images), ("chats", allchats), ("stats", stats), ("status", status)], 
                    "POST": [("parse", parse)] } 
        
        