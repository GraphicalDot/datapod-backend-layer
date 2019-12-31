

#-*- coding: utf-8 -*-

from .api import if_user_exists 
import os
from .variables import PLUGIN_NAME



class Plugin:
    def __init__(self, db_path):
        self.db_path = db_path
        self.plugin_name = PLUGIN_NAME
        self.routes = {"GET": [], 
                    "POST": [("user", if_user_exists)] } 
        
        