
import base64
import hashlib
import ipfsapi
from SettingsModule.settings import ipfs_ip, ipfs_port
from LoggingModule.logging import feynlog
import subprocess
import json
from SettingsModule import global_variables
import os
import time
from .filesystem import DecentralizeFilesystem
from EncryptionModule.generate_keys import GenerateKeys
from SettingsModule.settings import api_server
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import base64
from alert import Alert



class IPFS(DecentralizeFilesystem):
    
    ipfs_connection = None    
    ipfs_node_id = None 
    ipfs_public_key = None   
    ipfs_private_key = None   
    ipfs_connection = None
    def store_file(data):
        """
        Store the Identity encrypted with Public key 
        and hashes signed by digital signature and store them on blockchainDB.
        TODO: Encrypt this data, with the public key of this user, May be bigchaindb public key of this user
        TODO: You somehow force this file to be stored by atleast three other peers. If one of the peer goes down
            It should stores all the files to some other peers.
        """


        res = ipfs_connection.add_json({"cipher_text": data[0], "signature": data[1]})
        ##res{'Hash': 'QmWxS5aNTFEc9XbMX1ASvLET1zrqEaTssqt33rVZQCQb22', 'Name': 'test.txt'}
        print (res)
        return res


    def check_filesystem(self):
        feynlog.info("Checking if IPFs is running or not.")
        
        try:
            ##if ipfs_connection si working this impleies that this computer must have an ipfs config file
            ##This assumption might be wring later on
            ipfs_connection = ipfsapi.connect("localhost", 5001)
        except Exception as e:
            feynlog.error(f"""Something wrong happened while detection ipfs connection {e}.""")
            
        try:
            global_variables.ipfs_config = self.read_config_file()
            global_variables.ipfs_node_id = global_variables.ipfs_config["Identity"]["PeerID"]
        except Exception as e:
            print(e)
            global_variables.ipfs_node_id = None
            global_variables.ipfs_config = None
            feynlog.info(f"""Something wrong happened while reading ipfs config file {e}.""")
        return 
            
    def read_config_file(self):
        home_dir = os.path.expanduser('~')

        with open("%s/.ipfs/config"%home_dir) as __file:
            config = __file.read()
        json_data = json.loads(config)
        if not json_data:
            ##It might be a possibility that ipfs config got deleted after ipfs got a start
            ##in that case, though the config is not there, IPFS is runnning.
            ##need to stop IPFS
            subprocess.Popen(['systemctl', '--user', 'stop', 'ipfs'], stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()  

            p_status = p.wait()
            print ("Command output: " + output)

        return json_data

    def write_config_file(self, config):
        home_dir = os.path.expanduser('~')

        with open("%s/.ipfs/config"%home_dir, "w") as __file:
            json.dumps(config, __file)
        return 
    

    def delete_config_file(self):
        home_dir = os.path.expanduser('~')
        file_path = "%s/.ipfs/config"%home_dir

        subprocess.Popen(['rm', "-rf", file_path])
        return




    def initiate_filesystem(self):
        ##subprocess.call is blocking while subprocess popen is non blocking 
        subprocess.call(['systemctl', '--user', 'stop', 'ipfs'])
        subprocess.call(['ipfs', 'init'])
        subprocess.call(['systemctl', '--user', 'start', 'ipfs'])
        subprocess.call(['systemctl', '--user', 'enable', 'ipfs'])
        subprocess.call(['ipfs', 'config', 'Addresses.Gateway', '/ip4/0.0.0.0/tcp/9001'])
        subprocess.call(['ipfs', 'config', 'Addresses.API', '/ip4/0.0.0.0/tcp/5001'])
        subprocess.call(['ipfs', 'config','--json', 'Experimental.FilestoreEnabled', 'true'])
        

    def repeated_user(self, remote_config):
        ##remote_ipfs_config, which we got as a response from the api
        ##three cases, first one if thaty ipfs is running with the same node id as users's
        ##second case if ipfs is not running
        ##third is ipfs is running with the same node id as users
        feynlog.debug("The user is a repeated user with username %s and password %s"%(global_variables.username, global_variables.password))
        if global_variables.ipfs_config:
            if global_variables.ipfs_config["Identity"]["PeerID"] == remote_config["ipfs_config"]["Identity"]["PeerID"]:
                feynlog.debug("The node id and remote node is for this user is same")
                ##in case the ipfs node stopped because of some unknown reasons
                subprocess.call(['systemctl', '--user', 'start', 'ipfs'])
        
        else:
            self.write_config_file(self, read_config_file)
            self.initiate_filesystem()

        global_variables.encryption_public_key = remote_config["encryption_keys"]["public_key"]
        global_variables.encryption_private_key = remote_config["encryption_keys"]["private_key"]
        global_variables.passphrase = remote_config["encryption_keys"]["passphrase"]



        return 

    def new_user(self):
        feynlog.debug("The use is a new user")
        #Two cases, if ipfs is ruuning and other is ipfs in not running
        if global_variables.ipfs_config:
            feynlog.debug("But ipfs configuration exists, probably from some other user")        
            ##ig ipfs is running
            p = subprocess.Popen(['systemctl', '--user', 'stop', 'ipfs'], stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()  
            p_status = p.wait()
            self.delete_config_file()
        
        self.initiate_filesystem()
        encryption_class = GenerateKeys()
        private_key, public_key, passphrase  = encryption_class.make_rsa_keys_with_passphrase()
        global_variables.encryption_public_key = public_key.decode("utf-8")
        global_variables.encryption_private_key = private_key.decode("utf-8")
        global_variables.passphrase  = passphrase


        ##This is to reload the config file and id into global vairables.
        self.check_filesystem()

        data={"username": global_variables.username, "config_file": self.read_config_file(), 
                                "encryption_keys": {"private_key": private_key.decode("utf-8"), "public_key": public_key.decode("utf-8"), "passphrase": passphrase}}
        feynlog.debug(f"""New variables for this user {data}""")

        r = requests.post("%sdecentralizefilesystem"%api_server, data=json.dumps(data), headers={'Authorization': global_variables.app_token})
        feynlog.debug(r.json())


        feynlog.debug(global_variables.ipfs_public_key)
        feynlog.debug(global_variables.ipfs_private_key)
        return 


    def share_with_user(self, public_key):
        """
        Instantiate a new Genertekeys instance with public key of another user.
        Encrypt aes with this public key to enable decryption on this side.
        """



    def retrieve_file(file_name=None, uri=None):
        """
        Retrieve file on the basis of the file_name or uri
        """
        return 

    def retrieve_directory_contents(self, dir_name=None, uri=None):
        """
        Retrieve directory contents from the directory name or on the basis of the 
        uri fo the diretory storage
        """

        return 




    def list_file_directories(self, user_id):
        """
        List file or directories stored by the user on ditributed file system
        """
        return 


    def store_data(self, file_data, file_name, file_size, private_key=None, public_key=None, passphrase =None) :
        message = self.encrypt_data(file_data, file_name, file_size, private_key=None, public_key=None, passphrase =None)
        ipfs_connection = ipfsapi.connect("localhost", 5001)
        feynlog.debug("IPFS connection established")

        ipfs_file_hash = ipfs_connection.add_json(message)
        ipfs_connection.pin_add(ipfs_file_hash)


        feynlog.debug("IPHS hash that was stored is %s"%ipfs_file_hash)

        data = {"file_name": message["file_name"], "file_size": message["file_size"], "ipfs_hash": ipfs_file_hash, 
                "encryption_key": message["encryption_key"], "username": global_variables.username,
                "file_hash": message["file_hash"], "user_id": global_variables.user_id
        }

        r = requests.post("%sstorage"%api_server, data=data, headers={'Authorization': global_variables.app_token})
        feynlog.debug(r.json())
        Alert(title='Feynmen error message', text=r.json()["message"])

        return 


    def encrypt_data(self, file_path, file_name, file_size, private_key=None, public_key=None, passphrase =None):

        
        if not public_key and not private_key:
            public_key = global_variables.encryption_public_key
            private_key = global_variables.encryption_private_key
            passphrase = global_variables.passphrase
        bob = GenerateKeys(
                        passphrase= passphrase,
                        public_key=public_key, 
                        private_key=private_key)
            

        ##this will make an aes ke and set as a class vairable aes key
        aes_key = bob.make_aes_key()
        
        encrypted_aes_key = bob.get_encrypted_aes_key(public_key)

        feynlog.debug("AES KEY ===", aes_key)
        feynlog.debug("Encrypted AES KEY ===", encrypted_aes_key)

        with open(file_path, "rb") as f:
            file_data = f.read()
        
        file_ciphertext = bob.encrypt(file_data)

        signature = bob.create_signer(file_data)


        aes_base64_bytes = base64.b64encode(encrypted_aes_key)

        aes_base64_string = aes_base64_bytes.decode("UTF-8")

        message = {"signature": signature, "file_name": file_name, "file_hash": hashlib.sha256(file_data).hexdigest(),
                        "encryption_key": aes_base64_string,  
                        "file_size": os.path.getsize(file_path), "file_data": file_ciphertext.decode("utf-8"), "time": time.time()}

        feynlog.debug("The encryption has been completed successfully")
        for key in message.keys():
            feynlog.debug("key is %s and type is %s"%(key, type(message[key])))
        #feynlog.debug("This is ht emessage after encryption %s"%message)
        return message


        
        ##https://github.com/burke-software/simple-asymmetric-python/blob/master/simple_asym/asymmetric_encryption.py


    def encryption_public_key(self, message, private_key, public_key):
        #https://medium.com/@raul_11817/rsa-with-cryptography-python-library-462b26ce4120
        message = message.encode('ascii')
        ciphertext = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
                )
            )

        ciphertext  = str(base64.b64encode(ciphertext), encoding='utf-8')

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


if __name__ == "__main__":
    _class = IPFS()