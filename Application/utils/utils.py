
#-*- coding:utf-8 -*-

import pytz
import datetime
import os
from functools import wraps
from errors_module.errors import APIBadRequest


def timezone_timestamp(naive_timestamp, timezone):
    tz_kolkata = pytz.timezone(timezone)
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp


def month_aware_time_stamp(naive_timestamp=None): 
     tz_kolkata = pytz.timezone('Asia/Kolkata') 
     time_format = "%Y-%m-%d %H:%M:%S" 
     if naive_timestamp: 
         aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp)) 
     else: 
         naive_timestamp = datetime.datetime.now() 
         aware_timestamp = tz_kolkata.localize(naive_timestamp) 
     return {"timestamp": aware_timestamp.strftime(time_format + " %Z%z"), "year": aware_timestamp.year, "month": aware_timestamp.month} 


def folder_size(path='.'): 
    total = 0 
    for entry in os.scandir(path): 
        if entry.is_file(): 
            total += entry.stat().st_size 
        elif entry.is_dir(): 
            total += folder_size(entry.path) 
    return total 


##This decorator checks whether the app is running in testing or production stage
##This decorator will be used to ban the usage of some apis in production phase
def check_production():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            #is_authorized = check_request_for_authorization_status(request)

            if not request.app.config.TESTING_MODE:
                raise APIBadRequest("This API cant be executed in Production environment")
            response = await f(request, *args, **kwargs)
            return response
          
        return decorated_function
    return decorator

