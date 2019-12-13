

#-*- coding: utf-8 -*-
from .api import get_tables, store_permissions
        
routes = {"GET": [ ("get_tables", get_tables)], 
                    "POST": [("store_permissions", store_permissions)] } 
        