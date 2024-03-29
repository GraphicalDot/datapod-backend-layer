


import os
import sys
from Crypto.Cipher import AES

def generate_aes_key(number_of_bytes): 
     #return get_random_bytes(number_of_bytes) 
     return os.urandom(number_of_bytes) 


def aes_encrypt(key, file_bytes): 
     #return encrypt_CTR_MODE(key, file_bytes) 
      
     ##The nonce and the tag generated will be exactly 16 bytes 
     #ciphertext, tag, nonce = aes_encrypt(key, file_bytes) 
     #ciphertext = b"".join([tag, ciphertext, nonce]) 
     #The AES_GCM encrypted file content 
     #secret = binascii.hexlify(ciphertext) 
     if isinstance(file_bytes, str): 
         file_bytes = file_bytes.encode() 
     cipher = AES.new(key, AES.MODE_GCM) 
     ciphertext, tag = cipher.encrypt_and_digest(file_bytes) 
     nonce = cipher.nonce 
     return b"".join([tag, ciphertext, nonce]) 


def aes_decrypt(key, ciphertext):

    if isinstance(ciphertext, str):
        ciphertext = ciphertext.encode()
    tag, nonce = ciphertext[:16], ciphertext[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    decrypted_text = cipher.decrypt_and_verify(ciphertext[16:-16], tag)
    return decrypted_text
