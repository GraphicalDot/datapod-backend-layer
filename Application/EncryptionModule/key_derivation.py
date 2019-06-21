import os
from Crypto.Protocol.KDF import scrypt
KEY_LENGTH = 32
N = 2**16 ##meant for ram
R = 10
P = 10
import binascii
import bcrypt

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)






def generate_bcrypt(password):
    if isinstance(password, str):
        password = password.encode()
    hashed =bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed


def check_bcrypt(password: str, hashed_password: str):
    if isinstance(password, str):
        password = password.encode()

    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode()

    logger.warning(password)
    logger.warning(hashed_password)
    if bcrypt.checkpw(password, hashed_password):
        return True
    return False




def generate_scrypt_key(password, salt=None):
    ##return bytes of keys, returns list in case of keys > 1
    if not salt:
        salt = os.urandom(16)
    keys = scrypt(password,  salt, KEY_LENGTH, N, R, P, 1)
    return keys, salt