

#-*- coding: utf-8 -*-
from .api import get_tables
        
routes = {"GET": [ ("get_tables", get_tables)], 
                    "POST": [] } 
        