
import os
import pathlib
import subprocess
from EncryptionModule.symmetric import generate_aes_key
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

p = str(pathlib.Path(os.getcwd()))
home = os.path.expanduser("~")

datapod_dir = os.path.join(home, ".Datapod")


keys_dir = os.path.join(datapod_dir, "Keys")


key = generate_aes_key(32)



if not os.path.exists(keys_dir):
    logging.warning("Creating encryption keys Directory")
    os.makedirs(keys_dir)


if not os.path.exists(f"{keys_dir}/encryption.key"):
    logging.warning("Generating new key for encryption")
    with open(f"{keys_dir}/encryption.key", "wb") as fileobj:
        fileobj.write(key)


#openssl rand -out .key 32


user_data_path = os.path.join(datapod_dir, "data")


db_dir_path = os.path.join(datapod_dir, "database")
#db_dir_path = "/home/feynman/Desktop/database"
archive_path = os.path.join(datapod_dir, "archive")


HOST = "localhost"
PORT = 8000
DEBUG = True