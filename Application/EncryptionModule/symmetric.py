


import os
import sys
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
KEY_LENGTH = 32
N = 2**16 ##meant for ram
R = 10
P = 10


def generate_scrypt_key(password, salt=None):
    ##return bytes of keys, returns list in case of keys > 1
    if not salt:
        salt = os.urandom(16)
    keys = scrypt(password,  salt, KEY_LENGTH, N, R, P, 1)
    return keys, salt


def aes_encrypt(key, file_bytes):
    ##The nonce and the tag generated will be exactly 16 bytes
    ##ciphertext, tag, nonce = aes_encrypt(key, file_bytes)
    ##ciphertext = b"".join([tag, ciphertext, nonce])
    ##The AES_GCM encrypted file content
    ##secret = binascii.hexlify(ciphertext)
    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode()
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(file_bytes)
    nonce = cipher.nonce
    return tag+ciphertext+nonce

def aes_decrypt(key, ciphertext):

    if isinstance(ciphertext, str):
        ciphertext = ciphertext.encode()
    tag, nonce = ciphertext[:16], ciphertext[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    decrypted_text = cipher.decrypt_and_verify(ciphertext[16:-16], tag)
    return decrypted_text
