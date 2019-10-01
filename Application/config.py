
import os
import pathlib
import subprocess
from EncryptionModule.symmetric import generate_aes_key
from errors_module.errors import APIBadRequest
from database_calls.initialize_tables import intialize_db
from database_calls.coderepos.github.initialize import coderepos_github_initialize
from database_calls.facebook.initialize import facebook_initialize
from database_calls.twitter.intiialize import twitter_initialize
from database_calls.credentials import update_datasources_status 
from loguru import logger

__VERSION__ = "0.12-Beta"

home = os.path.expanduser("~")
MAIN_DIR = os.path.join(home, ".datapod")
LOGFILE = os.path.join(MAIN_DIR, "applogs.log")
logger.add(LOGFILE, retention="2 days")  # Cleanup after some time




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


DB_Object, Logs, Backup, Credentials, Emails, Purchases, Images, CryptCreds, CryptoExgBinance, \
    Datasources, EmailAttachment,IndexEmailContent, Reservations   = intialize_db(os.path.join(DB_PATH, "database.db"))

GITHUB_TBL, GITHUB_CREDS_TBL = coderepos_github_initialize(DB_Object)
FB_CREDS_TBL, FB_IMAGES_TBL =  facebook_initialize(DB_Object)
TWITTER_TBL, TWITTER_INDEXED_TBL, TweetAccountData =  twitter_initialize(DB_Object)


"""

########update_datasources_status(Datasources , "BACKUP", "backup" ,80, "Backup Completed", "SETUP_COMPLETED")
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
    #db_dir_path = "/home/feynman/Desktop/database"
    BACKUP_PATH = BACKUP_PATH

    URL = None



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
    DB_OBJECT = DB_Object
    LOGS_TBL = Logs
    BACKUPS_TBL = Backup
    CREDENTIALS_TBL = Credentials
    DATASOURCES_TBL = Datasources
    EMAILS_TBL = Emails
    PURCHASES_TBL = Purchases
    IMAGES_TBL = Images
    CODE_GITHUB_TBL =GITHUB_TBL
    CODE_GITHUB_CREDS_TBL = GITHUB_CREDS_TBL
    CRYPTO_CRED_TBL = CryptCreds 
    CRYPTO_EXG_BINANCE = CryptoExgBinance
    EMAIL_ATTACHMENT_TBL = EmailAttachment
    INDEX_EMAIL_CONTENT_TBL = IndexEmailContent
    TWITTER_INDEXED_TBL = TWITTER_INDEXED_TBL
    TWITTER_ACC_TBL = TweetAccountData
    RESERVATIONS_TBL = Reservations
    FB_CREDS_TBL= FB_CREDS_TBL 
    FB_IMAGES_TBL = FB_IMAGES_TBL
    TWITTER_TBL = TWITTER_TBL
    TWITTER_SSE_TOPIC = "TWITTER_PROGRESS"
    DB_OBJECT = DB_Object
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_ITEMS_NUMBER = 50 #the default number of items that should be returned in the api
    #TAR_SPLIT_SIZE = 524288 #size of the files in which the backup tar file will be broken
    TAR_SPLIT_SIZE = 512 #size of the files in which the backup tar file will be broken
    LANGUAGE = "english"
    #DATASOURCES_CODE = {"PURCHASES": 1, "RESERVATIONS": 2, "CRYPTO_BINANCE": 51, "EMAIL": 3, "IMAGES": 4, "REPOSITORY_GITHUB": 61}
    DATASOURCES_CODE = {"TAKEOUT": 1, "FACEBOOK": 2, "WHATSAPP": 3, "INSTAGRAM": 4, "CRYPTO": 5, "REPOSITORY": {"GITHUB": 6}, "TWITTER": 8, "BACKUP": 80}
    STATES = ["COMPLETED", "PROGRESS", 'STARTED', "NULL", "SETUP_COMPLETED"]



#openssl rand -out .key 32
class DevelopmentConfig(Config):   
    URL = "https://jadrlk2ok9.execute-api.ap-south-1.amazonaws.com/"
    LOGIN = f"{URL}Production/users/login"
    DELETE_USER = f"{URL}Production/users/delete_user"
    SIGNUP = f"{URL}Production/users/signup" 
    CONFIRM_SIGN_UP = f"{URL}Production/users/confirm-signup"
    CHANGE_MFA_SETINGS = f"{URL}Production/users/mfa-settings"
    ASSOCIATE_MFA = f"{URL}Production/users/associate-mfa"
    VERIFY_MFA = f"{URL}Production/users/verify-mfa"
    POST_LOGIN_MFA = f"{URL}Production/users/post-login-mfa"
    AWS_CREDS = f"{URL}Production/users/temp-credentials"
    FORGOT_PASS = f"{URL}Production/users/forgot-password"
    CHECK_MNEMONIC = f"{URL}Production/mnemonics/check-mnemonic" ##required username and mnemonic_sha_256 with auth token

    RESEND_CODE = f"{URL}Production/users/resend-code"
    CHANGE_PASSWORD = f"{URL}Production/users/change-password"
    CONFIRM_FORGOT_PASS = f"{URL}Production/users/confirm-password"
    PROFILE = f"{URL}Production/users/profile"
    RENEW_REFRESH_TOKEN = f"{URL}Production/users/renew-refresh-token"
    LOGOUT = f"{URL}Production/users/log-out"
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