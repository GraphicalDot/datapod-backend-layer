

##all the code related to adding an ew datasource
#-*- coding:utf-8 -*- 

from sanic import Blueprint
from .takeout  import TAKEOUT_BP
from .instagram_ds import INSTAGRAM_BP
from .facebook_ds import FACEBOOK_BP
from .browsers import BROWSER_HISTORY_BP
from .github import GITHUB_BP
from .crypto import C_BP
DATASOURCES_BP = Blueprint.group(TAKEOUT_BP, INSTAGRAM_BP, BROWSER_HISTORY_BP, 
                            FACEBOOK_BP, GITHUB_BP, C_BP, 
                            url_prefix="/datasources")
