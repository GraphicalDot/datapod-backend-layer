
import os
import pathlib
import subprocess
from EncryptionModule.symmetric import generate_aes_key
from errors_module.errors import APIBadRequest
from database_calls.initialize_tables import intialize_db
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

home = os.path.expanduser("~")
MAIN_DIR = os.path.join(home, ".datapod")
USER_INDEX = f"{MAIN_DIR}/user.index"
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
    Datasources, EmailAttachment,IndexEmailContent    = intialize_db(os.path.join(DB_PATH, "database.db"))


##########-------------------------------------------------------###########

def os_command_output(command:str, final_message:str) -> str:

    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        line = process.stdout.readline()
        if not line:
            logging.info(final_message)
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
    LOGS_TBL = Logs
    BACKUPS_TBL = Backup
    CREDENTIALS_TBL = Credentials
    DATASOURCES_TBL = Datasources
    EMAILS_TBL = Emails
    PURCHASES_TBL = Purchases
    IMAGES_TBL = Images
    CRYPTO_CRED_TBL = CryptCreds 
    CRYPTO_EXG_BINANCE = CryptoExgBinance
    EMAIL_ATTACHMENT_TBL = EmailAttachment
    INDEX_EMAIL_CONTENT_TBL = IndexEmailContent
    DB_OBJECT = DB_Object
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_ITEMS_NUMBER = 50 #the default number of items that should be returned in the api
    #TAR_SPLIT_SIZE = 524288 #size of the files in which the backup tar file will be broken
    TAR_SPLIT_SIZE = 512 #size of the files in which the backup tar file will be broken
    



#openssl rand -out .key 32
class DevelopmentConfig(Config):   
    URL = "https://jadrlk2ok9.execute-api.ap-south-1.amazonaws.com/"
    LOGIN = f"{URL}Production/users/login"
    SIGNUP = f"{URL}Production/users/signup" 
    CONFIRM_SIGN_UP = f"{URL}Production/users/confirm-signup"
    CHANGE_MFA_SETINGS = f"{URL}Production/users/mfa-settings"
    ASSOCIATE_MFA = f"{URL}Production/users/associate-mfa"
    VERIFY_MFA = f"{URL}Production/users/verify-mfa"
    POST_LOGIN_MFA = f"{URL}Production/users/post-login-mfa"
    AWS_CREDS = f"{URL}Production/users/temp-credentials"
    FORGOT_PASS = f"{URL}Production/users/forgot-password"
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