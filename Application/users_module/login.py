
import requests
import json
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from errors_module.errors import APIBadRequest
from database_calls.credentials import store_credentials, get_credentials
from functools import wraps
from jose import jwt, JWTError 
import pytz
import datetime
import dateutil
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__name__)


USERS_BP = Blueprint("user", url_prefix="/user")


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



def id_token_validity():
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




            try:
                id_token = result["id_token"].decode()
                refresh_token = result["refresh_token"].decode()
                username = result["username"]
            except Exception as e:
                
                logger.error("User must have signed out, Please Login again")
                raise APIBadRequest("Please Login again")


            payload = jwt.get_unverified_claims(id_token)

            time_now = datetime.datetime.fromtimestamp(revoke_time_stamp(timezone=request.app.config.TIMEZONE))
            time_expiry = datetime.datetime.fromtimestamp(payload["exp"])
            rd = dateutil.relativedelta.relativedelta (time_expiry, time_now)

            logger.warning("Difference between now and expiry of id_token")
            logger.warning(f"{rd.years} years, {rd.months} months, {rd.days} days, {rd.hours} hours, {rd.minutes} minutes and {rd.seconds} seconds")

            if rd.minutes < 20:
                logger.error("Renewing id_token, as it will expire soon")
                id_token = update_tokens(request, username, refresh_token)
          
            if isinstance(id_token, bytes):
                id_token = id_token.decode()

            response = await f(request, id_token, username, *args, **kwargs)
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


            username = result["username"].decode()
            response = await f(request,  username, *args, **kwargs)
            return response
          
        return decorated_function
    return decorator







@USERS_BP.post('/temp_credentials')
@id_token_validity()
async def temp_credentials(request, id_token, username):
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    
    r = requests.post(request.app.config.AWS_CREDS, data=json.dumps({"id_token": id_token}))
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json({
        'error': False,
        'success': True,
        "data": result["data"]
       })



@USERS_BP.post('/login')
async def login(request):

    request.app.config.VALIDATE_FIELDS(["username", "password"], request.json)

    r = requests.post(request.app.config.LOGIN, data=json.dumps({"username": request.json["username"], "password": request.json["password"]}))
    result = r.json()
    logger.info(result)
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    store_credentials(request.app.config.CREDENTIALS_TBL, request.json["username"],  result["data"]["id_token"], 
                 result["data"]["access_token"], result["data"]["refresh_token"])
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": None,
        "data": {
            "id_token": result["data"]["id_token"],
            "refresh_token": result["data"]["refresh_token"],
            "access_token": result["data"]["access_token"]
        }})



def update_tokens(request, username, refresh_token):
    logger.warning("Updating tokens for the user with the help of refresh token")
    # result = get_credentials(request.app.config.CREDENTIALS_TBL)
    # logger.info(result)
    # if not result:
    #     logger.error("Credentials aren't present, Please Login again")
    logger.info(username)
    logger.info(refresh_token)
        
    r = requests.post(request.app.config.RENEW_REFRESH_TOKEN, data=json.dumps({"username": username, "refresh_token": refresh_token}))
    logging.info(r.text)
    result = r.json()
    logger.info(result)

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest("Please login again")
    

    ##Updating credentials table of the user
    store_credentials(request.app.config.CREDENTIALS_TBL, username, 
               result["data"]["id_token"], 
                result["data"]["access_token"], refresh_token)
    
    logger.success("tokens are renewed")
    return result["data"]["id_token"]


@USERS_BP.post('/sign_up')
async def signup(request):
    request.app.config.VALIDATE_FIELDS(["email", "password", "name", "username"], request.json)

    if len(request.json["password"]) <8:
        logger.error("Password length should be greater than 8")
        raise APIBadRequest("Password length should be greater than 8")

    r = requests.post(request.app.config.SIGNUP, data=json.dumps({ "email": request.json["email"],
                "password": request.json["password"], 
                "name": request.json["name"],
                "username": request.json["username"]}))
    result = r.json()
    logger.info(result)

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json(
        {
        'error': False,
        'success': True,
        "message": result["message"],
        "data": None
        })



@USERS_BP.post('/confirm_signup')
async def confirm_signup(request):
    request.app.config.VALIDATE_FIELDS(["username", "code"], request.json)

    r = requests.post(request.app.config.CONFIRM_SIGN_UP, data=json.dumps({"username": request.json["username"],
                "code": request.json["code"]}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    return response.json(
        {
        'error': False,
        'success': True,
        "message": result["message"],
        "data": None
        })




@USERS_BP.post('/backup_credentials')
async def aws_temp_creds(request):
    request.app.config.VALIDATE_FIELDS(["token", "email", "password"], request.json)

    r = requests.post(request.app.config.AWS_CREDS, data=json.dumps({
                    "email": request.json["email"], 
                    "password": request.json["password"]}), 
                    headers={"Authorization": request.json["token"]})
    
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": None,
        "data": result["data"]
        })

    


@USERS_BP.get('/forgot_password')
@username()
async def forgot_password(request, username):
    r = requests.post(request.app.config.FORGOT_PASS, data=json.dumps({"username": username}))
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json(
        {
        'error': False,
        'success': True,
        "message": None,
        "data": result["message"]
        }) 


@USERS_BP.get('/new_password')
@username()
async def set_new_password(request):
    request.app.config.VALIDATE_FIELDS(["new_password", "validation_code"], request.json)

    r = requests.post(request.app.config.CONFIRM_FORGOT_PASS, data=json.dumps({
                "username": request.json["username"], 
                "password": request.json["new_password"], 
                "code":  request.json["validation_code"] 
                }))

    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    

    return response.json(
        {
        'error': False,
        'success': True,
        "message": None,
        "data": result["message"]
        }) 


@USERS_BP.post('/associate_mfa')
async def associate_mfa(request):
    request.app.config.VALIDATE_FIELDS(["session"], request.json)

    if type(request.json["enabled"]) != bool:
        raise APIBadRequest("Enabled must be boolean")

    r = requests.post(request.app.config.ASSOCIATE_MFA, data=json.dumps({"session": request.json["session"]}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json({
        'error': False,
        'success': True,
       })


@USERS_BP.post('/verify_mfa')
@username()
async def verify_mfa(request):
    request.app.config.VALIDATE_FIELDS(["session", "code"], request.json)

    if type(request.json["enabled"]) != bool:
        raise APIBadRequest("Enabled must be boolean")

    r = requests.post(request.app.config.VERIFY_MFA, data=json.dumps({"session": request.json["session"], 
        "username": username, "code": request.json["code"]
    }))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json({
        'error': False,
        'success': True,
        "session_token": data["session_token"]
       })


@USERS_BP.post('/post_login_mfa')
@username()
async def post_login_mfa(request):
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """
    
    request.app.config.VALIDATE_FIELDS(["session", "code"], request.json)

    r = requests.post(request.app.config.POST_LOGIN_MFA, data=json.dumps({"session": request.json["session"], 
        "username": username, "code": request.json["code"]
    }))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json({
        'error': False,
        'success': True,
        "data": result["data"]
       })



@USERS_BP.post('/mnemonics')
@id_token_validity()
async def mnemonics(request, id_token, username):
    
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    request.app.config.VALIDATE_FIELDS(["mnemonic", "key_index"], request.json)

    if type(request.json["enabled"]) != bool:
        raise APIBadRequest("Enabled must be boolean")


    r = requests.post(request.app.config.MNEMONIC_KEYS, data=json.dumps({"mnemonic": request.json["mnemonic"], 
        "key_index": request.json["key_index"]}), headers={"Authorization": id_token})

    try:
        result = r.json()
    except Exception:
        raise APIBadRequest(f"Errror in gettig keys for the index {request.json['key_index']}")

    return response.json({
        'error': False,
        'success': True,
        "data": result
       })


@USERS_BP.post('/profile')
@id_token_validity()
async def profile(request, id_token, username):
    
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    r = requests.post(request.app.config.PROFILE, data=json.dumps({"username": username}), 
        headers={"Authorization": id_token})
    
    result = r.json()
    if r.json["error"]:
        raise APIBadRequest(result["message"])

    return response.json({
        'error': False,
        'success': True,
        "data": result["data"]
       })

@USERS_BP.post('/logout')
@id_token_validity()
async def logout(request, id_token, username):
    
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    r = requests.post(request.app.config.LOGOUT, data=json.dumps({"username": username}), 
        headers={"Authorization": id_token})
    
    result = r.json()
    if r.json["error"]:
        raise APIBadRequest(result["message"])

    store_credentials(request.app.config.CREDENTIALS_TBL, username, 
               result["data"]["id_token"], 
                "", "")
    
    return response.json({
        'error': False,
        'success': True,
        "data": result["data"]
       })