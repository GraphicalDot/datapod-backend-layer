
import requests
import json
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from errors_module.errors import APIBadRequest
from database_calls.credentials import store_credentials, get_credentials
from functools import wraps

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


USERS_BP = Blueprint("user", url_prefix="/user")

def id_token_validity():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            #is_authorized = check_request_for_authorization_status(request)

            result = get_credentials(request.app.config.CREDENTIALS_TBL)
            logging.info(result)
            if not result:
                logger.error("Credentials aren't present, Please Login again")
                raise APIBadRequest("Credentials aren't present, Please Login again")

            response = await f(request, result["id_token"].decode(), *args, **kwargs)
            return response
            # if is_authorized:
            #     # the user is authorized.
            #     # run the handler method and return the response
            #     response = await f(request, *args, **kwargs)
            #     return response
            # else:
            #     # the user is not authorized. 
            #     return json({'status': 'not_authorized'}, 403)
        return decorated_function
    return decorator


@USERS_BP.post('/temp_credentials')
@id_token_validity()
async def temp_credentials(request, id_token):
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    # result = get_credentials(request.app.config.CREDENTIALS_TBL)
    # logging.info(result)
    # if not result:
    #     raise APIBadRequest("Credentials aren't present, Please Login again")
    
    # request.app.config.VALIDATE_FIELDS(["id_token"], request.json)

    # if type(request.json["enabled"]) != bool:
    #     raise APIBadRequest("Enabled must be boolean")

    r = requests.post(request.app.config.AWS_CREDS, data=json.dumps({"id_token": id_token}))
    result = r.json()
    logging.info(result)

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
    logging.info(result)
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    store_credentials(request.app.config.CREDENTIALS_TBL, request.json["username"], 
                request.json["password"], result["data"]["id_token"], 
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




def update_tokens(request):
    result = get_credentials(request.app.config.CREDENTIALS_TBL)
    logging.info(result)
    if not result:
        logger.error("Credentials aren't present, Please Login again")
    
    r = requests.post(request.app.config.LOGIN, data=json.dumps({"username": result["username"], "password": result["password"]}))
    result = r.json()
    logging.info(result)
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    store_credentials(request.app.config.CREDENTIALS_TBL, request.json["username"], 
                request.json["password"], result["data"]["id_token"], 
                result["data"]["access_token"], result["data"]["refresh_token"])
    logger.success("tokens are renewed")
    return 


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
    logging.info(result)

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
async def forgot_password(request):
    request.app.config.VALIDATE_FIELDS(["email"], request.json)
    r = requests.post(request.app.config.FORGOT_PASS, data=json.dumps({"email": request.json["email"]}))
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
async def set_new_password(request):
    request.app.config.VALIDATE_FIELDS(["email", "new_password", "validation_code"], request.json)

    r = requests.post(request.app.config.CONFIRM_FORGOT_PASS, data=json.dumps({
                "email": request.json["email"], 
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
async def verify_mfa(request):
    request.app.config.VALIDATE_FIELDS(["session", "username", "code"], request.json)

    if type(request.json["enabled"]) != bool:
        raise APIBadRequest("Enabled must be boolean")

    r = requests.post(request.app.config.VERIFY_MFA, data=json.dumps({"session": request.json["session"], 
        "username": request.json["username"], "code": request.json["code"]
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
async def post_login_mfa(request):
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """
    
    request.app.config.VALIDATE_FIELDS(["session", "username", "code"], request.json)

    if type(request.json["enabled"]) != bool:
        raise APIBadRequest("Enabled must be boolean")

    r = requests.post(request.app.config.POST_LOGIN_MFA, data=json.dumps({"session": request.json["session"], 
        "username": request.json["username"], "code": request.json["code"]
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
async def mnemonics(request):
    
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    request.app.config.VALIDATE_FIELDS(["mnemonic", "key_index", "id_token"], request.json)

    if type(request.json["enabled"]) != bool:
        raise APIBadRequest("Enabled must be boolean")


    r = requests.post(request.app.config.MNEMONIC_KEYS, data=json.dumps({"mnemonic": request.json["mnemonic"], 
        "key_index": request.json["key_index"]}), headers={"Authorization": request.json["id_token"]})

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
async def profile(request):
    
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """

    request.app.config.VALIDATE_FIELDS(["username", "id_token"], request.json)

    r = requests.post(request.app.config.PROFILE, data=json.dumps({"username": request.json["username"]}), 
        headers={"Authorization": request.json["id_token"]})
    
    result = r.json()
    if r.json["error"]:
        raise APIBadRequest(result["message"])

    return response.json({
        'error': False,
        'success': True,
        "data": result["data"]
       })