

#-*- coding: utf-8 -*-

from .db_initialize import initialize
from .api import parse, images, allchats, stats, status




class Routes:
    def __init__(self, db_object):
        self.db_object = db_object
        creds_table, images_table, other_posts, content =  initialize(self.db_object)
        self.datasource_name = "facebook"
        self.config  = { 
                "creds_table": creds_table,
                "image_table" : images_table,
                "other_posts": other_posts,
                "content": content,
                "code": hash("facebook")%10000,                 
        }
        
        self.routes = {"GET": [("images", images), ("chats", allchats), ("stats", stats), ("status", status)], 
                    "POST": [("parse", parse)] } 
        
        