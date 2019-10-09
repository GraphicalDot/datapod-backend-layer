

#-*- coding: utf-8 -*-

from .db_initialize import initialize

creds_table, images_table =  initialize(DB_Object)

SSE_CHANNEL = "FB_PROGRESS"



class FBConfig:
    FB_CREDS_TABLE = creds_table
    FB_IMG_TABLE  = images_table
    SSE_CHANNEL =  "FB_PROGRESS"
    DATASOURCE = "FACEBOOK"
    CODE = hash("FACEBOOK")%10000