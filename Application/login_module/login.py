
import requests
import json
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from errors_module.errors import APIBadRequest
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


USERS_BP = Blueprint("user", url_prefix="/user")


@USERS_BP.post('/login')
def login(request):
    request.app.config.VALIDATE_FIELDS(["email", "password"], request.json)

    r = requests.post(request.app.config.LOGIN, data=json.dumps({"email": request.json["email"], "password": request.json["password"]}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    return response.json(
        {
        'error': True,
        'success': False,
        "message": None,
        "data": {
            "id_token": result["data"]["id_token"],
            "refresh_token": result["data"]["refresh_token"]
        }})


@USERS_BP.post('/sign_up')
def signup(request):
    request.app.config.VALIDATE_FIELDS(["token", "email", "password", "name", "phone_number", "preferred_username"], request.json)

    if len(request.json["password"]) <8:
        logger.error("Password length should be greater than 8")
        raise APIBadRequest("Password length should be greater than 8")

    r = requests.post(request.app.config.SIGNUP, data=json.dumps({ "email": request.json["email"],
                "password": request.json["password"], 
                "name": request.json["name"],
                "phone_number": request.json["phone_number"],
                "preferred_username": request.json["preferred_username"]}))
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



@USERS_BP.post('/confirm_signup')
def confirm_signup(request):
    request.app.config.VALIDATE_FIELDS(["email", "validation_code"], request.json)

    r = requests.post(request.app.config.CONFIRM_SIGN_UP, data=json.dumps({"email": request.json["email"],
                "code": request.json["validation_code"]}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": result["message"],
        "data": None
        })



@USERS_BP.post('/profile')
def profile(request):
    request.app.config.VALIDATE_FIELDS(["token", "email"], request.json)

    r = requests.post(request.app.config.PROFILE, data=json.dumps({"email": request.json["email"]}), 
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



@USERS_BP.post('/backup_credentials')
def aws_temp_creds(request):
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
def forgot_password(request):
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
def set_new_password(request):
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


