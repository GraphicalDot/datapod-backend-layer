
import os
import requests
import json
import pathlib


#generat enew 32 byte key
#openssl rand -out sse-c.key 32

def generate_aes_key(number_of_bytes): 
     #return get_random_bytes(number_of_bytes) 
     return os.urandom(number_of_bytes) 

filepath = str(pathlib.Path(os.getcwd()))

import subprocess
from time import sleep

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


URL = "https://jadrlk2ok9.execute-api.ap-south-1.amazonaws.com/"

LOGIN = f"{URL}Production/login"
SIGNUP = f"{URL}Production/signup" 
CONFIRM_SIGN_UP = f"{URL}Production/confirm-sign-up"
PROFILE = f"{URL}Production/profile"
AWS_CREDS = f"{URL}Production/awstempcredentials"
FORGOT_PASS = f"{URL}Production/forgotpassword"
CONFIRM_FORGOT_PASS = f"{URL}Production/confirmpassword"
BUCKET_NAME = "datapod-backups"
AWS_DEFAULT_REGION = "ap-south-1"

def login(username, password):
    r = requests.post(LOGIN, data=json.dumps({"email": username, "password": password}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    

    return result["data"]["id_token"], result["data"]["refresh_token"]


def signup(token, email, password, name, phone_number, preferred_username):
    """
    {
        "email": "houzier.saurav@gmail.com",
        "password": "BIGwedding98@#",
        "name": "Saurav Verma",
        "phone_number": "+919958491323",
        "preferred_username": "graphicaldot"
        }
    """
    if len(password) <8:
        logger.error("Password length should be greater than 8")
        raise Exception("Password length should be greater than 8")

    r = requests.post(SIGNUP, data=json.dumps({ "email": email,"password": password, "name": name,
                "phone_number": phone_number,
                "preferred_username": preferred_username}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    
    return result["message"]


def confirm_signup(email, validation_code):
    r = requests.post(CONFIRM_SIGN_UP, data=json.dumps({"email": email,"code": validation_code}))
    result = r.json()

    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    
    return result["message"]



def profile(token, email):
    r = requests.post(PROFILE, data=json.dumps({"email": email}), headers={"Authorization": token})
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])

    logger.info(result["data"])

    return result["data"]

def aws_temp_creds(token, username, password):
    r = requests.post(AWS_CREDS, data=json.dumps({"email": username, "password": password}), headers={"Authorization": token})
    result = r.json()
    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    

    return result["data"]["identity_id"], result["data"]["access_key"], \
            result["data"]["secret_key"], result["data"]["session_token"] 


def forgot_password(email):
    r = requests.post(FORGOT_PASS, data=json.dumps({"email": email}))
    result = r.json()
    logger.info(result)
    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    

    return 

def set_new_password(email, new_password, validation_code):
    r = requests.post(CONFIRM_FORGOT_PASS, data=json.dumps({"email": email, "password": new_password, "code":  validation_code }))
    result = r.json()
    logger.info(result)
    if result.get("error"):
        logger.error(result["message"])
        raise Exception(result["message"])
    

    return 





    

if __name__ == "__main__":
    username = "houzier.saurav@gmail.com"
    password = "BIGwedding98@#"
    new_password  = "GOrootops98@#"
    validation_code = "524309"
    id_token, refresh_token= login(username, new_password)
    #profile(id_token, username)
    identity_id, access_key, secret_key, session_token = aws_temp_creds(id_token, username, new_password)
    
    
    #user_data_path = os.path.join(os.path.dirname(filepath), "userdata/filewise/facebook/")
    user_data_path =  "/home/feynman/.Datapod/data"
    if os.path.exists(user_data_path):
        logging.warning(f"The directory which will be synced to remote {user_data_path}")
    
    
    sync_directory(user_data_path, identity_id, access_key, secret_key, session_token)
    #forgot_password(username)
    
    #set_new_password(username, new_password, validation_code)