



from EncryptionModule.key_derivation import generate_scrypt_key
from EncryptionModule.symmetric import aes_decrypt, aes_encrypt
import binascii
from loguru import logger

def encrypt_mnemonic(password, mnemonic):
    """
    From the user password encrypt the mnemonic
    """

    key_bytes, hex_salt = generate_scrypt_key(password, salt=None)
    logger.info(f"Key_salt for the scrypt key from the user generated password {hex_salt}")
    encrypted_mnemonic = aes_encrypt(key_bytes, mnemonic)
    logger.info(f"encrypted_mnemonic is  {encrypted_mnemonic.hex()}")
    return hex_salt, encrypted_mnemonic.hex()


def decrypt_mnemonic(password, salt, encrypted_mnemonic):
    """
    From the user password decrypt the mnemonic
    """
    key_bytes, hex_salt = generate_scrypt_key(password, binascii.unhexlify( salt))
    unhexlified_mnemonic = binascii.unhexlify(encrypted_mnemonic)


    mnemonic = aes_decrypt(key_bytes, unhexlified_mnemonic)
    return mnemonic
    
    
