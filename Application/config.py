
import os
import pathlib
import subprocess
from EncryptionModule.symmetric import generate_aes_key
from errors_module.errors import APIBadRequest
from loguru import logger

__VERSION__ = "0.3.2"

home = os.path.expanduser("~")
MAIN_DIR = os.path.join(home, ".datapod")
LOGFILE = os.path.join(MAIN_DIR, "applogs.log")
logger.add(LOGFILE, retention="2 days", level="ERROR",  enqueue=True, backtrace=True, diagnose=True)  # Cleanup after some time




USER_INDEX = f"{MAIN_DIR}/user.index" #this file be creating when making backup and keeps record of all the files who are indexed for backup i.e changed or not
KEYS_DIR = os.path.join(MAIN_DIR, "keys")
USERDATA_PATH = os.path.join(MAIN_DIR, "userdata")
PARSED_DATA_PATH = os.path.join(USERDATA_PATH, "parsed")
RAW_DATA_PATH = os.path.join(USERDATA_PATH, "raw")


DB_PATH = os.path.join(USERDATA_PATH, "database")
#db_dir_path = "/home/feynman/Desktop/database"
BACKUP_PATH = os.path.join(MAIN_DIR, "backup")

for path in [MAIN_DIR, KEYS_DIR, USERDATA_PATH, PARSED_DATA_PATH, RAW_DATA_PATH, DB_PATH, BACKUP_PATH]:
    if not os.path.exists(path):
        logger.warning(f"Creating {path} Directory")
        os.makedirs(path)

##Intializing database and intialize the table object of the sqlite db


# DB_Object, Logs, Backup, Credentials, Emails, Purchases, Images, CryptCreds, CryptoExgBinance, \
#     Datasources, EmailAttachment,IndexEmailContent, Reservations   = intialize_db(os.path.join(DB_PATH, "database.db"))

# TWITTER_TBL, TWITTER_INDEXED_TBL, TweetAccountData =  twitter_initialize(DB_Object)


"""

########update_datasources_status(Datasources , "BACKUP", "backup",80, "Backup Completed", "SETUP_COMPLETED")
"""

# logger.info("Deleting tables")
# DB_Object.drop_tables([GITHUB_TBL])
# logger.info("tables deleted")

##########-------------------------------------------------------###########

def os_command_output(command:str, final_message:str) -> str:

    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        line = process.stdout.readline()
        if not line:
            logger.info(final_message)
            break
        yield line.decode().split("\r")[0]
    
def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise Exception("Improper JSON format")



# if not os.path.exists(f"{KEYS_DIR}/encryption.key"):
#     logging.warning("Generating new key for encryption")
#     with open(f"{KEYS_DIR}/encryption.key", "wb") as fileobj:
#         fileobj.write(key)

class Config:
    VERSION = __VERSION__
    MAIN_DIR = MAIN_DIR
    USER_INDEX = USER_INDEX
    KEYS_DIR = KEYS_DIR
    BACKUP_KEY_ENCRYPTION_FILE = os.path.join(KEYS_DIR, "encryption.key")
    USERDATA_PATH = USERDATA_PATH

    PARSED_DATA_PATH = PARSED_DATA_PATH
    RAW_DATA_PATH = RAW_DATA_PATH

    DB_PATH = DB_PATH    
    BACKUP_PATH = BACKUP_PATH

    HOST = "localhost"
    PORT = 8000
    DEBUG = True
    VALIDATE_FIELDS = None

    REQUEST_MAX_SIZE = 100000000         
    REQUEST_BUFFER_QUEUE_SIZE = 100
    REQUEST_TIMEOUT= 60
    RESPONSE_TIMEOUT= 60
    KEEP_ALIVE= True 
    KEEP_ALIVE_TIMEOUT=5
    GRACEFUL_SHUTDOWN_TIMEOUT = 15.0
    ACCESS_LOG = True   
    OS_COMMAND_OUTPUT  = os_command_output

 
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_ITEMS_NUMBER = 50 #the default number of items that should be returned in the api
    #TAR_SPLIT_SIZE = 524288 #size of the files in which the backup tar file will be broken
    TAR_SPLIT_SIZE = 512 #size of the files in which the backup tar file will be broken
    LANGUAGE = "english"
    STATES = ["COMPLETED", "PROGRESS", 'STARTED', "NULL", "SETUP_COMPLETED"]
    DEFAULT_SYNC_FREQUENCY = "5 8 * * 0"


#openssl rand -out .key 32
class DevelopmentConfig(Config):   
    URL = "ek14dw5898.execute-api.ap-south-1.amazonaws.com"
    STAGE = "v1"
    SIGNUP = f"https://{URL}/{STAGE}/user/signup"     
    LOGIN = f"https://{URL}/{STAGE}/user/login"     
    LOGOUT = f"https://{URL}/{STAGE}/user/logout"
    CONFIRM_SIGN_UP = f"https://{URL}/{STAGE}/user/confirm_sign_up"
    CHANGE_PASSWORD = f"https://{URL}/{STAGE}/user/change_password"
    FORGOT_PASSWORD = f" https://{URL}{STAGE}/user/forgot_password"


    CONFIRM_FORGOT_PASS = f"https://{URL}/{STAGE}/user/confirm_forgot_password"
    FORGOT_PASS = f"https://{URL}/{STAGE}/user/forgot_password"
    RENEW_REFRESH_TOKEN = f"https://{URL}/{STAGE}/user/renew_refresh_token"
    RESEND_CODE = f"https://{URL}/{STAGE}/user/resend_registration_code"
    TEMPORARY_S3_CREDS = f"https://{URL}/{STAGE}/user/temporary_s3_creds"


    TIMEZONE  = 'Asia/Kolkata' #TODO: THis should be selected by users to findout Timezone and must be saved in sqlite3
    MNEMONIC_KEYS = f"{URL}Production/mnemonics/get-keys"
    CHECK_MNEMONIC = f"{URL}Production/mnemonics/check-mnemonic"
    UPDATE_USER = f"{URL}Production/users/update-user"
    AWS_S3 = {"bucket_name": "datapod-backups","default_region": "ap-south-1"}
    HOST = "localhost"
    PORT = 8000
    DEBUG = True
    TESTING_MODE= True ##this mode decides whther it is in Testing stage or not, for production make it False
    VALIDATE_FIELDS = validate_fields

config_object = DevelopmentConfig