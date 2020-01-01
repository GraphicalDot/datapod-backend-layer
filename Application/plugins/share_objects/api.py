
import requests
import json
import subprocess
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from loguru import logger
import os
import binascii
import time
from errors_module.errors import MnemonicRequiredError
from errors_module.errors import APIBadRequest, PathDoesntExists
from loguru import logger
import subprocess
import shutil
import aiomisc
##imported from another major module
import boto3
from Crypto.Cipher import AES # pycryptodome
from Crypto import Random
import struct
import zipfile
import tempfile
import uuid
from datasources.datapod_users.variables import DATASOURCE_NAME as USER_DATASOURCE_NAME
from EncryptionModule.symmetric import generate_aes_key
from EncryptionModule.asymmetric import encrypt_w_pubkey, decrypt_w_privkey
import boto3.session


async def if_user_exists(request):
    request.app.config.VALIDATE_FIELDS(["username"], request.json)

    r = requests.post(request.app.config.USER_EXISTS, data=json.dumps({"username": request.json["username"]}))

    result = r.json()
    if result.get("error"):
        logger.debug(result["message"])
        raise APIBadRequest(result["message"])

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "User has been found",
        "data": result["data"]
        })



async def upload_objects(request):
    """

    TODO: right now this function calling login API by fetching username and password from the users table
    Ideally this shouldnt be the case, this plugin must have permission the access users table and should 
    only be able to fetch id_token or refresh_token, username and password of the user shouldnt be handed 
    over to the application 
    """

    creds = request.app.config[USER_DATASOURCE_NAME]["tables"]["creds_table"].select().dicts()
    request.app.config.VALIDATE_FIELDS(["file_list", "public_key", "username"], request.json)


    othr_username = request.json["username"]
    othr_user_public_key = request.json["public_key"]
    if len(othr_user_public_key) != 66:
        raise APIBadRequest("Incorrect length of user's public key")





    file_list = request.json["file_list"]

    if len(file_list) == 0:
        raise APIBadRequest("Empty file list is not supported")


    logger.debug(file_list)
    logger.debug(type(file_list))
    for file in  file_list:
        if not os.path.exists(file):
            raise APIBadRequest(f"file {file} doesnt exists on this host machine")


    if not creds:
        raise APIBadRequest("User is not logged in")
    
    creds = list(creds)[0]
    #r = requests.post(request.app.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))

    if othr_username == creds["username"]:
        raise APIBadRequest("Cant share file with him/herself")


    r = requests.post(request.app.config.TEMPORARY_S3_CREDS, data=json.dumps({"id_token": creds["id_token"].decode()}), headers={"Authorization": creds["id_token"].decode()})

    result = r.json()
    
    if result.get("message") == 'The incoming token has expired':
        return response.json({"error": True, "sucess": False, "msessage": "The id token has expired, Please login again", "data": None}, status=401)

    if result.get("error"):
        logger.error(result["message"])
        raise APIBadRequest(result["message"])
    
    identity_id, access_key, secret_key, session_token = result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]


    ##setting aws environment
    set_aws_environment(access_key, secret_key, session_token, request.app.config.AWS_S3["default_region"])


    ##crete temporary files 
    temp_zipfile = tempfile.NamedTemporaryFile('wb', suffix='.zip', delete=False)
    temp_encrypted_zipfile = tempfile.NamedTemporaryFile('wb', suffix='.encrypted.zip', delete=False)
    logger.debug(f"Path of temp_zipfile {temp_zipfile.name}")
    logger.debug(f"Path of temp_zipfile {temp_encrypted_zipfile.name}")

    await zip_files(file_list, temp_zipfile.name)
    logger.debug(f"Zip file creation at  {temp_zipfile.name} completed")
    
    iv, original_size, encryption_key = await encrypt_file(temp_zipfile.name, temp_encrypted_zipfile.name)
    logger.debug(f"iv {iv} original_size {original_size} encryption_key {encryption_key}")
    encrypted_key = encrypt_w_pubkey(encryption_key, othr_user_public_key)


    ##The name of the file when uploaded 
    remote_file_name = str(uuid.uuid4())

    object_key_name = await put_file("datapod-shared", encrypted_key, othr_user_public_key, creds["username"], othr_username, identity_id,  iv, temp_encrypted_zipfile.name, original_size, remote_file_name)
    
    logger.debug("file has been uploaded")
    remove_temporary_file(temp_zipfile.name)

    remove_temporary_file(temp_encrypted_zipfile.name)
    logger.debug("Temporary files has been deleted")

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Success hai dude",
        "data": None
        })




@aiomisc.threaded_separate
def put_file(bucket_name, encrypted_key, othr_user_public_key, username, othr_username, identity_id,  iv, upload_filename_path, unencrypted_file_size, filename):
    """
    client = boto3.client('s3', 'us-west-2')
    transfer = S3Transfer(client)
    # Upload /tmp/myfile to s3://bucket/key
    transfer.upload_file('/tmp/myfile', 'bucket', 'key')

    # Download s3://bucket/key to /tmp/myfile
    transfer.download_file('bucket', 'key', '/tmp/myfile')

    More examples could be found here 
    https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/s3/transfer.html
    """

    #'x-amz-key-v2': base64.b64encode(ciphertext_blob).decode('utf-8'),

    key_name = f"{identity_id}/{othr_username}-{filename}"

    metadata = {
        'x-amz-iv':  binascii.hexlify(iv).decode(),
        'x-amz-cek-alg': 'AES/CBC/PKCS5Padding',
        'x-amz-unencrypted-content-length': str(unencrypted_file_size),
        'x-amz-shared-with': othr_user_public_key,
        'x-amz-aes_key': binascii.hexlify(encrypted_key).decode(),
        'x-amz-username' : othr_username,
        'x-amz-source-username': username
    }

    s3client = boto3.client('s3')
    s3transfer = boto3.s3.transfer.S3Transfer(s3client)
    s3transfer.upload_file(upload_filename_path, bucket_name, key_name, extra_args={'Metadata': metadata})
    return key_name







def set_aws_environment(access_key, secret_key, session_token, region):
        os.environ['AWS_ACCESS_KEY_ID'] = access_key # visible in this process + all children
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key # visible in this process + all children
        os.environ['AWS_SESSION_TOKEN'] = session_token # visible in this process + all children
        os.environ["AWS_DEFAULT_REGION"] = region
        return





@aiomisc.threaded_separate
def zip_files(file_list, output_file_path):
    ##file_list is the list of files with complete path

    zipfilename =  str(uuid.uuid4())
    zipf = zipfile.ZipFile(output_file_path, 'w', zipfile.ZIP_DEFLATED)
    
    for file in file_list:
        zipf.write(file)
    return



def remove_temporary_file(file_name):
    try:
        os.remove(file_name)
    except Exception as e:
        logger.error(f"couldnt remove temporary  file {file_name} with error {e}")
    return 


@aiomisc.threaded_separate
def encrypt_file(in_filename_path, out_filename_path, chunksize=16*1024):
    iv = Random.new().read(AES.block_size) ##this will also be in bytes
    original_size = os.stat(in_filename_path).st_size # unencrypted length of the input filename
    encryption_key = generate_aes_key(32) ##this will be in bytes

    with open(in_filename_path, 'rb') as infile:
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)

        # 3 cases here for padding at the end of file:
        # - we get a full chunk of 16. pass it through.
        # - we get a partial chunk at EOF. we pad it up to 16. generally speaking each byte is the byte number, so if we have 7 bytes, the following nine are "07 07 07 07 07 07 07 07 07".
        # - we get a zero-byte chunk at EOF. This means the file was a perfect multiple of 16, but padding means the end of the file should be padded because IDK why but that's how it's done. See url below:
        #
        # the extra padding at zero-byte EOF: http://security.stackexchange.com/a/29997
        #   "The above problem is solved by knowing that you always pad your data, no matter the length."
        with open(out_filename_path, 'wb') as outfile:
            last_chunk_length = 0
            while True:
                chunk = infile.read(chunksize)
                last_chunk_length = len(chunk)
                if last_chunk_length == 0 or last_chunk_length < chunksize:
                    break
                outfile.write(cipher.encrypt(chunk))

            # write the final padding
            length_to_pad = 16 - (last_chunk_length % 16)
            # not py2 compatible
            # chunk += bytes([length])*length
            chunk += struct.pack('B', length_to_pad) * length_to_pad
            outfile.write(cipher.encrypt(chunk))

    return iv, original_size, encryption_key



@aiomisc.threaded_separate
def generate_presigned_url(bucketname, identityid, keyname, region_name, expiration_time):
    session = boto3.session.Session(region_name='eu-central-1')
    s3Client = session.client('s3')
    url = s3Client.generate_presigned_url('get_object', Params = {'Bucket': bucketname, 'Key': keyname}, ExpiresIn=expiration_time)








    # for (name, last_modified) in backup_folders:
    #     logger.debug(f"Name of archival {name} and last_modified {last_modified} ")
    #     size = self.get_size(bucket_name, self.identity_id+"/"+name)
    #     logger.debug(f"Size archival {size} ")

def decrypt_file(self, key, in_filename, iv, original_size, out_filename, chunksize=16*1024):
    with open(in_filename, 'rb') as infile:
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))
            outfile.truncate(original_size)




























class S3Backup(object):


    async def __init__(self, config):
        """
        number is the percentage number which will be sent in sse message, 
        Then number has already been incremented by the backup scripts above, 

        """
        self.config = config
        self.bucket_name = config.AWS_S3['bucket_name']

        #self.credentials = get_credentials(config.CREDENTIALS_TBL)
        self.credentials = await get_credentials(self.config[USER_DATASOURCE_NAME]["tables"]["creds_table"])
        if not self.credentials:
            raise APIBadRequest("User is not logged in")
        
        self.credentials = list(self.credentials)[0]
        ##in this temporary file, private key is now written

        if not self.credentials["encryption_key"]:
            raise MnemonicRequiredError()




        self.encryption_key = binascii.unhexlify(self.credentials["encryption_key"].encode())


        self.identity_id, self.access_key, self.secret_key, self.session_token =  await self.aws_temp_creds()
        
     

        os.environ['AWS_ACCESS_KEY_ID'] = self.access_key # visible in this process + all children
        os.environ['AWS_SECRET_ACCESS_KEY'] = self.secret_key # visible in this process + all children
        os.environ['AWS_SESSION_TOKEN'] = self.session_token # visible in this process + all children
        os.environ["AWS_DEFAULT_REGION"] = self.config.AWS_S3["default_region"]


    def remove_temporary_dir(self, dirpath):
        shutil.rmtree(dirpath)
        return 

    def remove_temporary_file(self, file_name):
        try:
            os.remove(file_name)
        except Exception as e:
            logger.error(f"couldnt remove temporary  file {file_name} with error {e}")
        return 


    def list_s3_archives(self, bucket_name=None):
        if not bucket_name:
            bucket_name = self.config.AWS_S3['bucket_name']


        s3 = boto3.resource('s3')
        my_bucket = s3.Bucket(bucket_name)
        
        ##this will have backup folders name i.e archievalname of the forms December-25-2019_12-55-17
        backup_folders = set()
        for obj in my_bucket.objects.filter(Prefix=f"{self.identity_id}/"): 
            s3_key = obj.key 
            filename = os.path.basename(s3_key)  
            foldername = os.path.dirname(os.path.dirname(s3_key)).split("/")[-1]     
            backup_folders.add((foldername, obj.last_modified.strftime("%d-%m-%Y")))
        
        backup_folders = list(backup_folders)
        logger.info(backup_folders)
        # result = map(lambda x: {"name": bucket_name + "/" + x[0], "last_modified": x[1]}, backup_folders)

        return [ {"archive_name": name, "last_modified": last_modified, 
                    "size": self.get_size(bucket_name, self.identity_id+"/"+name)
                    } 
                for (name, last_modified) in backup_folders]



    def get_size(self, bucket, path=None):
    
        ##if path is None
        ##then get the whole size of the users directory at s3 i.e the identity_id
        if not path:
            path = self.identity_id            

        # logger.debug(f"bucker is <<{bucket}>> and path is <<{path}>>")
        # s3 = boto3.resource('s3')
        # my_bucket = s3.Bucket(bucket)
        # total_size = 0



        # for obj in my_bucket.objects.filter(Prefix=path):
        #     total_size = total_size + obj.size

        s3 = boto3.resource('s3')
        total_size = 0
        bucket = s3.Bucket(bucket)
        for key in bucket.objects.filter(Prefix=f'{path}/'): 
            total_size = total_size + key.size


        return humanize.naturalsize(total_size)

    async def aws_temp_creds(self):
        creds = await get_credentials(self.config[USER_DATASOURCE_NAME]["tables"]["creds_table"])


        if not creds:
            raise APIBadRequest("User is not logged in")
        
        creds = list(creds)[0]
        r = requests.post(self.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
    
        result = r.json()
        if result.get("error"):
            logger.error(result["message"])
            raise APIBadRequest(result["message"])
        
        r = requests.post(self.config.TEMPORARY_S3_CREDS, data=json.dumps({"id_token": result["data"]["id_token"]}), headers={"Authorization": result["data"]["id_token"]})

        result = r.json()
        if result.get("error"):
            logger.error(result["message"])
            raise APIBadRequest(result["message"])
        return result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]


    async def sync_backup(self, datasource_name, src_path, backup_name):
        raise Exception("Please subclass and overide this method")

























class BotoBackup(S3Backup):


    async def sync_backup(self, datasource_name, src_path, backup_name):
        

        iv = Random.new().read(AES.block_size)
        target_directory = tempfile.mkdtemp() #    Caller is responsible for deleting the directory when done with it.
        for in_filename in os.listdir(src_path): ##list allfilenames in the input_directory
            in_filename_path = os.path.join(src_path, in_filename)##making the filename as the full path
            original_size = os.stat(in_filename_path).st_size # unencrypted length of the input filename
            
            """
            There are two types of files in this temporary archival directory for a particular datasource
            one ends with in just .sha512, these shouldnt be encrypted and shall be uploaded as it is
            The other ones needs encryption
            """
            
            if os.path.splitext(in_filename)[-1] != ".sha512": ##filter out files whose extension is 
                out_filename_path = os.path.join(target_directory, in_filename.replace(".tar", ".encrypted.tar")) ##making the output file name and inserting encrypted

                logger.debug(f"input filename is {in_filename} output dir is {out_filename_path}")
                
                logger.debug(f"iv <<{iv}>>")
                logger.debug(f"Original size <<{original_size}>>")
                await self.encrypt_file(in_filename_path, out_filename_path, iv, original_size, target_directory)
                ##Delete temporary files here to optimize storage , and then finally dlete the empty temporary directory
                await self.put_file(iv, out_filename_path, original_size,  backup_name, datasource_name)
            else:
                out_filename_path = os.path.join(target_directory, in_filename)
                await self.put_file(iv, in_filename_path, original_size,  backup_name, datasource_name)
            
            self.remove_temporary_file(out_filename_path)
    

        self.remove_temporary_dir(target_directory)
        logger.debug(f"Upload on s3 bucket for {datasource_name} is completed")
        return 






class AWSCliBackup(S3Backup):



    def encryption_key_file(self):
        encryption_key_file = tempfile.NamedTemporaryFile('wb', suffix='.txt')
        with open(encryption_key_file.name, "wb") as f:
            f.write(binascii.unhexlify(self.credentials["encryption_key"].encode()))
        return encryption_key_file



    def remove_temporary_file(self, file_name):
        try:
            os.remove(file_name)
        except Exception as e:
            logger.error(f"couldnt remove temporary archive file {file_name} with error {e}")
        return 


    async def sync_backup(self, src_path, backup_name):

        size = dir_size(src_path)
        # _key = generate_aes_key(32)

        # key = "".join(map(chr, _key))
        # print (key)
        # encryption_key_path = "/home/feynman/.Datapod/Keys/encryption.key"

        encryption_key_file = self.encryption_key_file()

        configure_command = f"aws configure set default.s3.max_bandwidth 15MB/s"
        for out in self.config.OS_COMMAND_OUTPUT(configure_command, "Limit upload speed"):
            logger.info (out)

        #sync_command = f"aws s3 sync --sse-c AES256 --sse-c-key fileb://{self.encryption_key_file.name} {self.config.BACKUP_PATH} s3://{self.config.AWS_S3['bucket_name']}/{self.identity_id}"
        sync_command = f"aws s3  mv --sse-c AES256 --sse-c-key fileb://{encryption_key_file.name} {src_path} s3://{self.config.AWS_S3['bucket_name']}/{self.identity_id}/{backup_name} --recursive"
        print (sync_command)

        for out in self.config.OS_COMMAND_OUTPUT(sync_command, "Files are in Sync"):
            # if self.number < 98:
            #     res = {"message": "BACKUP_PROGRESS", "percentage": self.number}
            #     await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
            #     self.number += 1
            #     await update_percentage(self.config[DATASOURCE_NAME]["tables"]["status_table"], "backup", self.number)
            logger.debug(f"Syncing on cloud  {out}")

        # res = {"message": "BACKUP_PROGRESS", "percentage": 100}
        # await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
        # await update_percentage(self.config[DATASOURCE_NAME]["tables"]["status_table"], "backup", 100)
        
        return size







# if __name__ == "__main__":
#     s3 = boto3.client('s3')
#     location_info = s3.get_bucket_location(Bucket="datapod-backups-beta")
#     bucket_region = location_info['LocationConstraint']

#     # kms = boto3.client('kms')
#     # encrypt_ctx = {"kms_cmk_id":kms_arn}

#     # key_data = kms.generate_data_key(KeyId=kms_arn, EncryptionContext=encrypt_ctx, KeySpec="AES_256")
#     new_iv = Random.new().read(AES.block_size)
#     size_infile = os.stat(infile).st_size # unencrypted length
#     outfile = infile + '.enc'

#     encrypt_file(key_data['Plaintext'], infile, new_iv, size_infile, outfile, chunksize=16*1024)
#     put_file(key_data['CiphertextBlob'], new_iv, encrypt_ctx, outfile, size_infile, bucket_name, key_name)