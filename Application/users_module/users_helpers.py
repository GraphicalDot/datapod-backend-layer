



from EncryptionModule.key_derivation import generate_scrypt_key


def encrypt_mnemonic(password, mnemonic):
    """
    From the user password encrypt the mnemonic
    """

    key_bytes, hex_salt = generate_scrypt_key(password, salt=None)
    encrypted_mnemonic = aes_encrypt(key_bytes, file_bytes)
    return hex_salt, encrypted_menmonic


def decrypt_mnemonic(password):
    """
    From the user password decrypt the mnemonic
    """
    pass