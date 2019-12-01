
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
import humanize
from   database_calls.db_profile import  get_datasources, count_datasources
from utils.utils import folder_size
import datetime
from loguru import logger
PROFILE_BP = Blueprint("profile", url_prefix="/")




@PROFILE_BP.get('profile')
async def profile(request):
    """
    Datasources information for the dashboard as in 
    how many datasources has been added and what are the details related to it
    """
    res = get_datasources(request.app.config.DATASOURCES_TBL)
    for entry in res:
        humanize_time = humanize.naturaltime(datetime.datetime.now() - entry["last_updated"])                                                                                                                                                                                                                       
        entry.update({"last_updated": humanize_time})
    
    return response.json(
        {
        'error': False,
        'success': True,
        "data": res,
        "message": None
        })



@PROFILE_BP.get('stats')
async def stats(request):
    """
    Stats abou the usr data stored on the datapod
    on his machine
    """
    res = get_datasources(request.app.config.DATASOURCES_TBL)
    number_of_files = sum([len(files) for r, d, files in os.walk(request.app.config.USERDATA_PATH)])
    size = humanize.naturalsize(folder_size(request.app.config.USERDATA_PATH))
    number_of_datasources = count_datasources(request.app.config.DATASOURCES_TBL)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"files": number_of_files, "size": size, "datasources": number_of_datasources},
        "message": None
        })


