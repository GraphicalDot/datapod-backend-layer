

##all the code related to adding an ew datasource
#-*- coding:utf-8 -*- 

from sanic import Blueprint
from .gmail_ds import GMAIL_BP

DATASOURCES_BP = Blueprint.group(GMAIL_BP, 
                            url_prefix="/datasources")
