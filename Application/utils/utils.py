
#-*- coding:utf-8 -*-

import pytz
import datetime
import os
from functools import wraps
from errors_module.errors import APIBadRequest
from database_calls.credentials import get_credentials,update_id_and_access_tokens
import requests
import json
from functools import wraps

import pytz
import datetime
import dateutil
from jose import jwt, JWTError 
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__name__)

def convert_type(value):
    if isinstance(value, bytes):
        logging.info(f"{value} is in bytes")
        value = value.decode()
    return value


def revoke_time_stamp(days=0, hours=0, minutes=0, timezone=None): 
    if not timezone:
        logger.error("Please specify valid timezone for your servers")
        raise APIBadRequest("Please specify valid timezone for your servers")
    tz_kolkata = pytz.timezone(timezone) 
    time_format = "%Y-%m-%d %H:%M:%S" 
    naive_timestamp = datetime.datetime.now() 
    aware_timestamp = tz_kolkata.localize(naive_timestamp) 
 
    ##This actually creates a new instance od datetime with Days and hours 
    _future = datetime.timedelta(days=days, hours=hours, minutes=minutes) 
    result = aware_timestamp + _future 
    return result.timestamp() 


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

def id_token_validity():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            #is_authorized = check_request_for_authorization_status(request)

            result = get_credentials(request.app.config.CREDENTIALS_TBL)
            #logger.info(f"Data from the credential table in id_token_validity decorator {result}")
            if not result:
                logger.error("Credentials aren't present, Please Login again")
                raise APIBadRequest("Credentials aren't present, Please Login again")




            try:
                id_token = convert_type(result["id_token"])
                access_token = convert_type(result["access_token"])
                refresh_token = convert_type(result["refresh_token"])
                username = result["username"]
                request["user_data"] = result
            except Exception as e:
                
                logger.error(f"User must have signed out, Please Login again with an error {e.__str__()}")
                raise APIBadRequest("Please Login again")


            payload = jwt.get_unverified_claims(id_token)

            time_now = datetime.datetime.fromtimestamp(revoke_time_stamp(timezone=request.app.config.TIMEZONE))
            time_expiry = datetime.datetime.fromtimestamp(payload["exp"])
            rd = dateutil.relativedelta.relativedelta (time_expiry, time_now)

            logger.warning("Difference between now and expiry of id_token")
            logger.warning(f"{rd.years} years, {rd.months} months, {rd.days} days, {rd.hours} hours, {rd.minutes} minutes and {rd.seconds} seconds")

            if rd.minutes < 20:
                logger.error("Renewing id_token, as it will expire soon")
                id_token = update_tokens(request.app.config, username, refresh_token)
          
            if isinstance(id_token, bytes):
                id_token = id_token.decode()

            response = await f(request, *args, **kwargs)
            return response
          
        return decorated_function
    return decorator




def username():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            #is_authorized = check_request_for_authorization_status(request)

            result = get_credentials(request.app.config.CREDENTIALS_TBL)
            logger.info(f"Data from the credential table in id_token_validity decorator {result}")
            if not result:
                logger.error("Credentials aren't present, Please Login again")
                raise APIBadRequest("Credentials aren't present, Please Login again")

            username = result["username"]
            if isinstance(username, bytes):
                username = username.decode()
            
            response = await f(request,  username, *args, **kwargs)
            return response
          
        return decorated_function
    return decorator



def update_tokens(config, username, refresh_token):
    logger.warning("Updating tokens for the user with the help of refresh token")
    # result = get_credentials(request.app.config.CREDENTIALS_TBL)
    # logger.info(result)
    # if not result:
    #     logger.error("Credentials aren't present, Please Login again")
    r = requests.post(config.RENEW_REFRESH_TOKEN, data=json.dumps({"username": username, "refresh_token": refresh_token}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest("Please login again")
    

    ##Updating credentials table of the user
    update_id_and_access_tokens(config.CREDENTIALS_TBL, 
                username,
               result["data"]["id_token"], 
                result["data"]["access_token"])
    
    logger.success("tokens are renewed")
    return result["data"]["id_token"]
