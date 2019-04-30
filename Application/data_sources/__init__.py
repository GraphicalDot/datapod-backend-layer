

##all the code related to adding an ew datasource
#-*- coding:utf-8 -*- 

from sanic import Blueprint
from .emails  import EMAILS_BP
from .instagram_ds import INSTAGRAM_BP
from .facebook_ds import FACEBOOK_BP
DATASOURCES_BP = Blueprint.group(EMAILS_BP, INSTAGRAM_BP, FACEBOOK_BP, 
                            url_prefix="/datasources")
