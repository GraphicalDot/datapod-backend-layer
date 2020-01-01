from Crypto.Random import get_random_bytes
import base64
import binascii
# from SSSA import sssa
import random
from ecies import encrypt, decrypt
import hashlib
from loguru import logger

def encrypt_w_pubkey(data, public_key):
    ##this encrypts the mnemonic witht he public key
    ##Mnemonic must be in bytes
    if isinstance(data, str):
        data = data.encode()


    try:
        encrypted_data =  encrypt(public_key, data)
    except Exception as e:
        logger.error(f"While encrypting data with publickey{public_key} and data {data} is {e}")
        raise Exception("Couldnt encrypt with public key")
    ##hex encoding aes key
    return encrypted_data



def decrypt_w_privkey(encrypted_data, private_key):
    ##this encrypts the mnemonic witht he public key
    data = binascii.unhexlify(encrypted_data)

    ##hex encoding aes key
    try:
        decrypted_data =  decrypt(private_key, data)
    except Exception as e:
        logger.error(f"While encrypting data with private key {private_key} and data {data} is {e}")
        raise Exception("Couldnt decrypt with private key")

    return decrypted_data