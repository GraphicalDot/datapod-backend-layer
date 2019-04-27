

##from sawtooth_signing import create_context
#from sawtooth_signing import CryptoFactory
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import base64
import typing
import ipfsapi
import json
import os
import string
import random
from cryptography.fernet import Fernet
##https://media.readthedocs.org/pdf/python-ipfs-api/latest/python-ipfs-api.pdf

from .exceptions import (
    MissingAESException, MissingRSAPrivateException, MissingRSAPublicException)


RSAKey = typing.TypeVar('RSAKey')
DEFAULT_MODULUS= 4096

class GenerateKeys(object):
    aes_cipher = None
    public_key = None
    private_key = None

    def __init__(self, passphrase=None, aes_key=None, public_key=None, private_key=None):
        self.private_key = None 
        self.public_key = None
        if aes_key:
            self.set_aes_key(aes_key)
        self.set_public_key(public_key)
        self.set_private_key(private_key, passphrase=passphrase)

    def _get_padding(self):
        return padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )


    def generate_keys(self, passphrase=None, bits=DEFAULT_MODULUS) -> typing.Tuple[bytes, bytes]:
        """
        Generate public privatekeys

        https://sawtooth.hyperledger.org/docs/core/releases/1.0/_autogen/sdk_submit_tutorial_python.html

        context = create_context('secp256k1')
        private_key = context.new_random_private_key()
        signer = CryptoFactory(context).new_signer(private_key)

        self.private_key_hex =  private_key.as_hex()
        self.signer_public_key=signer.get_public_key().as_hex(),
        return (private_key_hex, signer_public_key)

        """

        # generate private/public key pair
        self.private_key = rsa.generate_private_key(
            backend=default_backend(), 
            public_exponent=65537, 
            key_size=2048)

        # get public key in OpenSSH format
        self.public_key = self.private_key.public_key()
        
        if passphrase:
            encryption_alg = serialization.BestAvailableEncryption(
                passphrase.encode()
            )
            _format = serialization.PrivateFormat.PKCS8
        else:
            encryption_alg = serialization.NoEncryption()
            _format = serialization.PrivateFormat.TraditionalOpenSSL

        private = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM, 
            format=_format,
            encryption_algorithm=encryption_alg)


        public = self.public_key.public_bytes(
              encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

        # get private key in PEM container format
        
        """
        if save_keys:
            with open(self.private_filename, 'wb') as pem_out:
                pem_out.write(pem)

            with open(self.public_filename, 'wb') as pem_out:
                pem_out.write(pem_public)
    	    # decode to printable strings
            self.private_key_str = pem.decode('utf-8')
            self.public_key_str = pem_public.decode('utf-8')
            
            print('Private key = ')
            print(self.private_key_str)
            print('Public key = ')
            print(self.public_key_str)
        """
        return (private, public)



    def make_rsa_keys_with_passphrase(self, bits=DEFAULT_MODULUS) -> typing.Tuple[bytes, bytes, str]:
        """ Wrapper around make_rsa_keys that also generates a passphrase
        :param bits: Bits for pycrypto's generate function. Safe to ignore.
        :rtype: tuple (private, public, passphrase) """
        passphrase = self._generate_passphrase()
        private, public = self.generate_keys(passphrase=passphrase, bits=bits)
        return private, public, passphrase

    def set_private_key(self, private_key: typing.Union[bytes, str, RSAKey], passphrase=None) -> RSAKey:
        """ Set private key
        :param private_key: String or RSAPrivateKey object
        :param passphrase: Optional passphrase for encrypting the RSA private key
        :rtype: private key
        """
        if isinstance(private_key, (bytes, str)):
            private_key = self._force_bytes(private_key)
            if passphrase:
                passphrase = self._force_bytes(passphrase)
            self.private_key = serialization.load_pem_private_key(
                private_key,
                password=passphrase,
                backend=default_backend()
            )
        else:
            self.private_key = private_key
        return self.private_key

    def set_public_key(self, public_key: typing.Union[bytes, str, RSAKey]) -> RSAKey:
        """ Set public key
        :param public_key: String or RSAPublicKey object
        :rtype: public key
        """
        if isinstance(public_key, (bytes, str)):
            public_key = self._force_bytes(public_key)
            self.public_key = serialization.load_pem_public_key(
                public_key,
                backend=default_backend()
            )
        else:
            self.public_key = public_key
        return self.public_key
    
    def set_aes_key(self, aes_key: bytes):
        self.aes_key = aes_key
        self.aes_cipher = Fernet(self.aes_key)

    def set_aes_key_from_encrypted(self, ciphertext: bytes, use_base64=False):
        """ Set aes_key from an encrypted key
        A shortcut method for receiving a AES key that was encrypted for our
        RSA public key
        :param ciphertext: Encrypted version of the key (bytes or base64 string)
        :param use_base64: If true, decode the base64 string
        """
        if use_base64 is True:
            ciphertext = base64.b64decode(ciphertext)
        aes_key = self.rsa_decrypt(ciphertext)
        self.set_aes_key(aes_key)

    def get_encrypted_aes_key(self,
                              public_key: typing.Union[bytes, str, RSAKey],
                              use_base64=False) -> bytes:
        """ Get encrypted aes_key using specified public_key
        A shortcut method for sharing a AES key.
        :param public_key: The public key we want to encrypt for
        :param use_base64: Will result in the returned key to be base64 encoded
        :rtype: encrypted key (bytes or base64 string"""
        public_asym = GenerateKeys(public_key=public_key)
        encrypted_key = public_asym.rsa_encrypt(self.aes_key)
        if use_base64 is True:
            encrypted_key = base64.b64encode(encrypted_key)
        return encrypted_key

    def make_aes_key(self) -> bytes:
        """ Generate a new AES key
        :rtype: AES key string
        """
        key = self._generate_key()
        self.set_aes_key(key)
        return key

    def encrypt(self, plaintext: typing.Union[str, bytes]) -> bytes:
        """ Encrypt text using AES encryption.
        Requires public_key and aes_key to be set. aes_key may be generated with
        AsymCrypt.make_aes_key if you do not already have one.
        :param plaintext: text to encrypt
        :rtype: ciphertext string
        """
        plaintext = self._force_bytes(plaintext)
        if not self.aes_cipher:
            raise MissingAESException
        return self.aes_cipher.encrypt(plaintext)

    def decrypt(self, text: bytes):
        """ Decrypt ciphertext using AES encryption.
        Requires private_key and aes_key to be set. aes_key may have been
        generated with AsymCrypt.make_aes_key which should have been done at
        time or encryption.
        :param text: ciphertext to decrypt
        :rtype: decrypted text string
        """
        if not self.aes_cipher:
            raise MissingAESException
        return self.aes_cipher.decrypt(text)


    def rsa_encrypt(self, text: typing.Union[str, bytes], use_base64=False) -> bytes:
        """ Convert plain text to ciphertext
        :param text: Plaintext to encrypt. Accepts str or bytes
        :param use_base64: set True to return a base64 encoded unicode string
        (just for convenience)
        :type use_base64: Boolean
        :rtype: ciphertext bytes
        """
        text = self._force_bytes(text)
        if not self.public_key:
            raise MissingRSAPublicException
        ciphertext = self.public_key.encrypt(
            text,
            self._get_padding()
        )
        if use_base64 is True:
            ciphertext = base64.b64encode(ciphertext)
        return ciphertext

    def rsa_decrypt(self, ciphertext: bytes, use_base64=False) -> bytes:
        """ Convert ciphertext into plaintext
        :param ciphertext: Ciphertext to decrypt
        :param use_base64: set True to return a base64 encoded unicode string
        (just for convenience)
        :type use_base64: Boolean
        :rtype: plaintext bytes
        """

        if use_base64 is True:
            ciphertext = base64.b64decode(ciphertext)
        if not self.private_key:
            raise MissingRSAPrivateException
        plaintext = self.private_key.decrypt(
            ciphertext,
            self._get_padding()
        )
        return plaintext        


    def create_signer(self, message):
        """
        f = serialization.load_pem_private_key(
            private_key,
            password=string.encode(passphrase),
            backend=default_backend()
            )
        """
        data_to_sign = bytes(message, encoding='utf8') if not isinstance(message, bytes) else message

        signer = self.private_key.signer(
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
        hashes.SHA256()
            )

        signer.update(data_to_sign)
        signature = str(
                base64.b64encode(signer.finalize()),
            encoding='utf8'
        )
        return signature


    @staticmethod
    def encrypt_json(self, message, private_key, public_key):
    	#https://medium.com/@raul_11817/rsa-with-cryptography-python-library-462b26ce4120
        
        
        
        message = message.encode('ascii')

        data_to_sign = bytes(message, encoding='utf8') if not isinstance(message, bytes) else message

        signer = private_key.signer(
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
        hashes.SHA256()
            )

        signer.update(data_to_sign)
        signature = str(
                base64.b64encode(signer.finalize()),
            encoding='utf8'
        )
        return (ciphertext, signature)

    def _generate_key(self) -> bytes:
        return Fernet.generate_key()


    def _random_string(self, n:int) -> str:
        return "".join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(n))


    def _generate_passphrase(self, n=255) -> str:
        return self._random_string(n)


    def _force_bytes(self, text: typing.Union[str, bytes]) -> bytes:
        try:  # Encode if not already done
            text = text.encode()
        except AttributeError:
            pass
        return text


    def test_keys(self):
        """
        Test if the encryption and decryption process
        """












class GetUserDetails:

    def __init__(self, identity_image, self_image):
        """
        to check if there is a match between the image of the person and get
        the relevant details from the adhaar 

        """
        self.identity_image = identity_image
        self.self_image = self
        
        
        
        
    def adhaar(self):
        """
        If the identity_image is of kind adhaar
        
        TODO: Use any thirdparty of write your own functions for convolution neural nets to get the 
        similirity between the two
        True if there is a match in the identities 
        """


        return (fake.credit_card_number(), fake.address(), fake.name(), True)



if __name__ == "__main__":
    _instance = GenerateKeys()
    print (_instance.make_rsa_keys_with_passphrase())
    print ("Generating aes key", "\n\n")
    aes_key = _instance.make_aes_key()
    print (aes_key)
    print (aes_key.decode())
    #(ciphertext, signature) = _instance.encrypt_object("hey now, Dude how are you")
    #print (ciphertext, signature)
    #ipfs_object_hash = StoreDetails.storedetails((ciphertext, signature))

