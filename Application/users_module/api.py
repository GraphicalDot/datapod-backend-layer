
import requests
import json
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from errors_module.errors import APIBadRequest

from .users_helpers import encrypt_mnemonic, decrypt_mnemonic
from database_calls.credentials import store_credentials, get_credentials,\
            update_mnemonic, update_password_hash



from utils.utils import id_token_validity, username
from EncryptionModule.gen_mnemonic import generate_entropy, generate_mnemonic, child_keys
import hashlib
from loguru import logger

USERS_BP = Blueprint("user", url_prefix="/user")








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


@USERS_BP.get('/is_logged_in')
async def is_logged_in(request):
    """
    session is the session which you will get after enabling MFA and calling login api
    code is the code generated from the MFA device
    username is the username of the user
    """
    creds = get_credentials(request.app.config.CREDENTIALS_TBL)
    logger.info(creds)
    if not creds:
        raise APIBadRequest("User is not looged in")
    

    if not creds.get("id_token"):
        raise APIBadRequest("User is not looged in")
    

    return response.json({
        'error': False,
        'success': True,
        "data": None, 
        "message": "User is logged in"
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
    

    password_hash = hashlib.sha3_256(request.json["password"].encode()).hexdigest()

    store_credentials(request.app.config.CREDENTIALS_TBL, request.json["username"], password_hash, result["data"]["id_token"], 
                 result["data"]["access_token"], result["data"]["refresh_token"])
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Logged in successfully",
        "data": None, 
        # {
        #     "id_token": result["data"]["id_token"],
        #     "refresh_token": result["data"]["refresh_token"],
        #     "access_token": result["data"]["access_token"]
        # }
        })






@USERS_BP.post('/sign_up')
async def signup(request):
    request.app.config.VALIDATE_FIELDS(["email", "password", "name", "username"], request.json)

    for e in ["email", "password", "name", "username"]:
        logger.info(f"{e} and value is  {request.json[e]}")

    if len(request.json["password"]) <8:
        logger.error("Password length should be greater than 8")
        raise APIBadRequest("Password length should be greater than 8")

    data = {
            "email": request.json["email"],
            "password": request.json["password"],
            "name": request.json["name"],
            "username": request.json["username"]
        }

    logger.info(data)
    r = requests.post(request.app.config.SIGNUP, data=json.dumps(data))
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
    logger.info(result)
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    return response.json(
        {
        'error': False,
        'success': True,
        "message": result["message"],
        "data": result["data"]
        })




# @USERS_BP.post('/backup_credentials')
# async def aws_temp_creds(request):
#     request.app.config.VALIDATE_FIELDS(["token", "email", "password"], request.json)

#     r = requests.post(request.app.config.AWS_CREDS, data=json.dumps({
#                     "email": request.json["email"], 
#                     "password": request.json["password"]}), 
#                     headers={"Authorization": request.json["token"]})
    
#     result = r.json()
#     if result.get("error"):
#         logger.error(result["message"])
#         raise APIBadRequest(result["message"])
    
#     return response.json(
#         {
#         'error': False,
#         'success': True,
#         "message": None,
#         "data": result["data"]
#         })

    

@USERS_BP.post('/change_password')
@id_token_validity()
async def change_password(request):
    request.app.config.VALIDATE_FIELDS(["previous_password", "proposed_password"], request.json)
    
    ##check if the password matches with the password stored in the database
    password_hash = hashlib.sha3_256(request.json["previous_password"].encode()).hexdigest()
    
    if request.json["previous_password"] == request.json["proposed_password"]:
        raise APIBadRequest("Password should be different")



    if password_hash != request["user_data"]["password_hash"]:
        raise APIBadRequest("Password you have enetered is incorrect")

    r = requests.post(request.app.config.CHANGE_PASSWORD, 
            data=json.dumps({"previous_password": request.json["previous_password"],
                "proposed_password": request.json["proposed_password"],
                "access_token": request["user_data"]["access_token"]
            }))

    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    

    ##since the password has been updated on the remote db, 
    ##this password should also be updated in the localdatabase too
    new_password_hash = hashlib.sha3_256(request.json["proposed_password"].encode()).hexdigest()

    update_password_hash(request.app.config.CREDENTIALS_TBL, 
            request["user_data"]["username"], new_password_hash)
    
    return response.json(
        {
        'error': False,
        'success': True,
        "message": None,
        "data": result["message"]
        }) 

@USERS_BP.post('/forgot_password')
async def forgot_password(request):
    logger.info(f"API for forgot password {request.app.config.FORGOT_PASS}")
    request.app.config.VALIDATE_FIELDS(["username"], request.json)

    ##if the username entered is different from the username stored in the 
    ##database 
    result = get_credentials(request.app.config.CREDENTIALS_TBL)
    if result:
        logger.info("Credentials are present in the database")
        if result["username"] != request.json["username"]:
            logger.error("Regenerating password for a different username\
                                     is not allowed and not recommended")




    r = requests.post(request.app.config.FORGOT_PASS, 
            data=json.dumps({"username": request.json["username"]}))

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


@USERS_BP.post('/confirm_forgot_password')
async def set_new_password(request):
    request.app.config.VALIDATE_FIELDS(["proposed_password", "validation_code", "username"], request.json)

    ##check if the password matches with the password stored in the database

    r = requests.post(request.app.config.CONFIRM_FORGOT_PASS, data=json.dumps({
                "username": request.json["username"], 
                "newpassword": request.json["proposed_password"], 
                "code":  str(request.json["validation_code"])
                }))

    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    
    new_password_hash = hashlib.sha3_256(request.json["proposed_password"].encode()).hexdigest()

    update_password_hash(request.app.config.CREDENTIALS_TBL, 
    request.json["username"], new_password_hash)


    return response.json(
        {
        'error': False,
        'success': True,
        "message": result["message"],
        "data": None
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



@USERS_BP.get('/new_mnemonic')
async def new_mnemonic(request):
    return response.json({
        "error": True, 
        "success": False,
        "message": None,
        "data": {
            "mnemonic": generate_mnemonic(request.app.config.LANGUAGE)
        } 
    })

 

@USERS_BP.post('/update_user')
@id_token_validity()
async def update_user(request):
    """
    When the user is trying to access the feature of backup, 
    THe user has to finalize a mnemonic, whose hash will then be upload 
    on the remote API, 

    The password hash must be checked with the one stored in the credential tbl

    Simulateneously, A scrypt password will be genrated from the user password and 
    will be used to encrypt the user mnemonic
    """

    request.app.config.VALIDATE_FIELDS(["mnemonic", "password"], request.json)
    mnemonic = request.json["mnemonic"]
    if len(mnemonic.split()) != 12:
        raise APIBadRequest("Please enter a mnemonic of length 12, Invalid Mnemonic")


    ###check if the stored pass_hash is same as the password_hash of the password 
    ##given by the user
    password_hash = hashlib.sha3_256(request.json["password"].encode()).hexdigest()
    if password_hash != request["user_data"]["password_hash"]:
        raise APIBadRequest("Password do not match with the sotred password")



    if request["user_data"].get("mnemonic"):
        raise APIBadRequest("The mnemonic is already present")



    mnemonic_keys = child_keys(request.json["mnemonic"], 0)
    logger.info(mnemonic_keys)

    ##check mnemonic hash stored against user on the dynamodb
    mnemonic_sha_256=hashlib.sha3_256(request.json["mnemonic"].encode()).hexdigest()
    r = requests.post(request.app.config.CHECK_MNEMONIC, data=json.dumps({
                "username": request["user_data"]["username"], 
                "mnemonic_sha_256": mnemonic_sha_256,
                }), headers={"Authorization": request["user_data"]["id_token"]})

    if r.json()["error"]:
        raise APIBadRequest(r.json()["message"])


    ##Encrypting user mnemonic with the scrypt key generated from the users password
    hex_salt, encrypted_menmonic = encrypt_mnemonic(request.json["password"], mnemonic)

    mnemonic_sha3_256 = hashlib.sha3_256(request.json["mnemonic"].encode()).hexdigest()
    mnemonic_sha3_512 = hashlib.sha3_512(request.json["mnemonic"].encode()).hexdigest()

    if not r.json()["data"]:
        ##this implies that the mnemonic of the user has not been saved in the clod dynamodb
        ##we need to make an api call to save data of the user 
        logging.info("Saving user mnemonic hash on the dynamodb")

        ##updateing user details on the remote api with mnemonic sha3_256 and sha3_512 hash
        r = requests.post(request.app.config.UPDATE_USER, data=json.dumps({
                    "public_key": mnemonic_keys["public_key"], 
                    "username": request["user_data"]["username"], 
                    "sha3_256": mnemonic_sha3_256,
                    "sha3_512": mnemonic_sha3_512
                    }), headers={"Authorization": request["user_data"]["id_token"]})
    
        result = r.json()
        logging.info(result)

        if result.get("error"):
            logger.error(result["message"])
            raise APIBadRequest(result["message"])


    update_mnemonic(request.app.config.CREDENTIALS_TBL, 
                request["user_data"]["username"], 
                encrypted_menmonic, 
                hex_salt)

    return response.json({
        "error": True, 
        "success": False,
        "message": "Mnemonic has been saved and updated",
        "data": None
    })


@USERS_BP.post('/decrypt_mnemonic')
async def decrypt_user_mnemonic(request):
    """
    Api to decrypt mnemonic stored in the sqlite table, 
    Password is required to decrypt the mnemonic 

    """
    request.app.config.VALIDATE_FIELDS(["password"], request.json)
    credentials = get_credentials(request.app.config.CREDENTIALS_TBL)

    password_hash = hashlib.sha3_256(request.json["password"].encode()).hexdigest()

    if password_hash != credentials["password_hash"]:
        raise APIBadRequest("The password you have entered in incorrect")

    if not credentials.get("mnemonic"):
        raise APIBadRequest("No Encrypted Mnemonic present")

    mnemonic = decrypt_mnemonic(request.json["password"], credentials["salt"], credentials["mnemonic"])
    logger.info(f"THis is the decrypted mnemonic {mnemonic}")
    return response.json({
        "error": True, 
        "success": False,
        "message": "Mnemonic has been decrypted successfully",
        "data": {"mnemonic": mnemonic}
    })


# @USERS_BP.post('/check_mnemonic')
# @id_token_validity()
# async def check_mnemonic(request):
#     """

#     """
#     request.app.config.VALIDATE_FIELDS(["mnemonic"], request.json)
#     mnemonic = request.json["mnemonic"]
#     if len(mnemonic.split(" ")) != 12:
#         raise APIBadRequest("Please enter a mnemonic of length 12, Invalid Mnemonic")

#     ##check mnemonic hash stored against user on the dynamodb
#     mnemonic_sha_256=hashlib.sha3_256(request.json["mnemonic"].encode()).hexdigest()
#     r = requests.post(request.app.config.CHECK_MNEMONIC, data=json.dumps({
#                 "username": request["user_data"]["username"], 
#                 "mnemonic_sha_256": mnemonic_sha_256,
#                 }), headers={"Authorization": request["user_data"]["id_token"]})

#     if r.json()["error"]:
#         raise APIBadRequest(r.json()["message"])


#     try:
#         result = r.json()
#     except Exception as e:
#         raise APIBadRequest(f"Errror in checking mnemonic sanctity {e.__str__()}")

#     update_mnemonic(request.app.config.CREDENTIALS_TBL, username, mnemonic)
    
#     return response.json({
#         'error': False,
#         'success': True,
#         "data": result["message"]
#        })


@USERS_BP.post('/child_keys')
@id_token_validity()
async def mnemonics(request, id_token, username):
    
    """
    When a new pub/priv key pair needs to be generated, Password of the user is required 
    to decrypt the mnemonic stored on localstorage.
    """

    request.app.config.VALIDATE_FIELDS(["mnemonic", "key_index", "password"], request.json)

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