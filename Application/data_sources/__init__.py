

##all the code related to adding an ew datasource
#-*- coding:utf-8 -*- 

from sanic import Blueprint
from .instagram_ds import INSTAGRAM_BP
from .browsers import BROWSER_HISTORY_BP
from .github_ds import GITHUB_BP
from .crypto import C_BP
from .twitter_ds import TWITTER_BP
from .api import PROFILE_BP
DATASOURCES_BP = Blueprint.group(PROFILE_BP, INSTAGRAM_BP, BROWSER_HISTORY_BP, 
                             TWITTER_BP, GITHUB_BP, C_BP, 
                            url_prefix="/datasources")
