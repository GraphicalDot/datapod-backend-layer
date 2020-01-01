from abc import ABC,abstractmethod 
import os
import binascii
import subprocess
import time
import datetime
import platform
import tempfile
import requests
import json
import aiohttp
from sanic import response

from asyncinit import asyncinit
from errors_module.errors import MnemonicRequiredError
from errors_module.errors import APIBadRequest, PathDoesntExists
from loguru import logger
from .variables import DATASOURCE_NAME
from .db_calls import get_credentials, update_percentage
import subprocess
import shutil
import humanize
import aiomisc
##imported from another major module
from ..datapod_users.variables import DATASOURCE_NAME as USER_DATASOURCE_NAME
import boto3
from Crypto.Cipher import AES # pycryptodome
from Crypto import Random
import struct

def get_size(bucket, path):
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket)
    total_size = 0

    for obj in my_bucket.objects.filter(Prefix=path):
        total_size = total_size + obj.size

    return total_size

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def dir_size(dirpath):
    return subprocess.check_output(['du','-sh', dirpath]).split()[0].decode('utf-8')



class Backup(object):
    def __init__(self, config, full_backup):

        self.config = config
        self.full_backup = full_backup
        self.userdata_path = self.config.USERDATA_PATH
        
        ##file which keeps tracks of the data that has been backup last time
        self.user_index_dir = self.config.USER_INDEX_DIR


        ##subdirectories in userdata path which deals with raw, parsed and database path 
        ##for the userdata.
        self.parsed_data_path = self.config.PARSED_DATA_PATH
        
        
        #self.raw_data_path = os.path.join(self.config.RAW_DATA_PATH, "facebook")
        self.raw_data_path = self.config.RAW_DATA_PATH

        self.db_path = self.config.DB_PATH
        self.backup_path = self.config.BACKUP_PATH

        self.percentage = 1

    async def send_sse_message(self, message):
        res = {"message": message, "percentage": self.percentage}
        await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
        await update_percentage(self.config[DATASOURCE_NAME]["tables"]["status_table"], "backup", self.percentage)
        return 



    async def make_backup(self):
        """
        --level=0, for fullbackup
        --level=1, for incremental backup
        --listed_incremental is equivalent to -g
         --atime-preserve=system 
         brew install gnu-tar
        #tar --create --lzma --verbose --multi-volume --tape-length 102400  --file=MyArchive.tgz raw -g user.index
        With --newer you're simply updating/creating the archive with the files that have changed since the date you pass it.
        tar  --create --lzma --verbose  --file=MyArchive raw/facebook/facebook-sauravverma14473426
        """
        datasources = os.listdir(self.raw_data_path)
        logger.debug(datasources)
        if not datasources:
            raise APIBadRequest("The directory whose backup needs to be made is empty")



        archival_object = datetime.datetime.utcnow()
        archival_name = archival_object.strftime("%B-%d-%Y_%H-%M-%S")



        parent_destination_path = os.path.join(self.backup_path, archival_name) 


        s3_backup_instance = await BotoBackup(self.config)
            
        step = int(90/len(datasources))

        for (index, datasource_name) in enumerate(datasources):
            s3_folder_name = archival_name + "/" + datasource_name
            dst_path = os.path.join(self.backup_path, archival_name, datasource_name) 
            src_path = os.path.join(self.raw_data_path, datasource_name)
            # if not os.path.exists(dst_path):
            #     os.makedirs(dst_path)
            backup_archival_temporary_path = await self.create(src_path, dst_path, datasource_name)
            # # res = {"message": "Progress", "percentage": int(i*step)}
            # # await self.config["send_sse_message"](config, DATASOURCE_NAME, res)
            
            await s3_backup_instance.sync_backup(datasource_name, backup_archival_temporary_path, archival_name)
        
            ##the split archival for a datasource in a temporary folder hasnt been removed yet, removing it now
            self.remove_split_archival_dir(backup_archival_temporary_path)
            logger.debug(f"Now removing the split files present {backup_archival_temporary_path} ")
            self.percentage = (index +1)*step
            
            await self.send_sse_message(f"Archiving of {datasource_name} completed")
        
        self.percentage = 100
        await self.send_sse_message(f"Backup completed")
        
        return parent_destination_path, archival_name

    async def create(self, src_path, dst_path, datasource_name): 

        #temp = tempfile.NamedTemporaryFile('wb', suffix='.tar.lzma', delete=False)
        temp = tempfile.NamedTemporaryFile('wb', suffix='.tar.gz', delete=False)
        #temp = tempfile.TemporaryFile()

        
        # backup_path = f"{self.backup_path}/{archival_name}/backup.tar.lzma"

            

        ##this is the file under ~/.datapod/user_indexes for a corresponding datasource 
        ## which wil keep track of all the files which have been backed up previously
        user_index_file = os.path.join(self.user_index_dir, f"{datasource_name.lower()}.index")
        logger.debug(f"{datasource_name} This is the user_index_file {user_index_file}, used to create a compressed file at {temp.name} from a directory at {src_path} ")
        
        
        if platform.system() == "Linux":
            if self.full_backup:
                backup_command = f"tar  --create  --gzip --no-check-device --verbose  -f {temp.name} {src_path}"                                        
            else:
                backup_command = f"tar  --create  --gzip --no-check-device --verbose --listed-incremental={user_index_file} -f {temp.name} {src_path}"

        elif platform.system() == "Darwin":
            if self.full_backup:
                backup_command = f"gtar  --create  --lzma --no-check-device --verbose  -f {temp.name} {src_path}"
            else:
                backup_command = f"gtar  --create  --lzma --no-check-device --verbose --listed-incremental={user_index_file} -f {temp.name} {src_path}"

        else:
            raise APIBadRequest("The platform is not available for this os distribution")

        #backup_command = f"tar --create  --verbose --listed-incremental={user_index_file} --lzma {backup_path} {self.raw_data_path}"
        initial_time = int(time.time())
        next_time = initial_time+15


        for out in self.config.OS_COMMAND_OUTPUT(backup_command, "Backup"):
            if int(time.time()) >= next_time:
                # await self.send_sse_message(f"Archiving {out.split('/')[-1]} for {datasource_name}")
                logger.debug(f"Archiving {out.split('/')[-1]} for {datasource_name}")
                next_time += 10

        
        split_backup_dir = tempfile.mkdtemp()

        logger.debug(f"Now, splitting the single compressed file {temp.name} in a temporary directory {split_backup_dir}")
        
        async for msg in self.split(split_backup_dir, temp.name):
            # await self.send_sse_message(msg)
            logger.debug(msg)
        
        ##because temp.name will automatically be removed
        logger.debug(f"Now removing single comporessed file at {temp.name}")
        self.remove_temporary_archive(temp.name)

        return split_backup_dir


    def remove_split_archival_dir(self, dirpath):
        shutil.rmtree(dirpath)
        return 

    def remove_temporary_archive(self, file_name):
        logger.warning(f"Removing temporary backup file {file_name}")
        try:
            os.remove(file_name)
        except Exception as e:
            logger.error(f"couldnt remove temporary archive file {file_name} with error {e}")
        return 

    async def split(self, dst_path, file_path):
        ##TODO: filename in split command is fixed but it may change on the type of compression being used
        dir_name, file_name = os.path.split(file_path)

        with cd(dst_path):
            logger.debug(f"The directory where split is taking place {dst_path}")
            if platform.system() == "Linux":
                #command = "tar --tape-length=%s -cMv  --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.config.TAR_SPLIT_SIZE, dir_name, file_name)
                command = "split --bytes=%sMB %s backup.tar.gz.1"%(self.config.TAR_SPLIT_SIZE, file_path)
            elif platform.system() == "Darwin":
                command = "split -b %sm %s backup.tar.gz.1"%(self.config.TAR_SPLIT_SIZE, file_path)
                
                #command = "gtar --tape-length=%s -cMv --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.config.TAR_SPLIT_SIZE, dir_name, file_name)
            else:
                raise APIBadRequest("The platform is not available for this os distribution")

            for out in self.config.OS_COMMAND_OUTPUT(command, "Split"):
                yield (f"SPLIT in progress {out[-70:]}")

            for name in os.listdir("."):
                logger.info(f"Creating sha checksum for backup split file {name}")
                for out in self.config.OS_COMMAND_OUTPUT(f"sha512sum {name} > {name}.sha512", "sha checksum"):
                    yield (f"Creating sha checksum {out}")
        
            ##calculating the whole backup file tar 
            for out in self.config.OS_COMMAND_OUTPUT(f"sha512sum {file_path} > backup.sha512", "sha checksum"):
                yield (f"Creating sha checksum {out}")

        return 





@asyncinit
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
        # r = requests.post(self.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
    
        # result = r.json()
        # if result.get("error"):
        #     logger.error(result["message"])
        #     raise APIBadRequest(result["message"])
        
        r = requests.post(self.config.TEMPORARY_S3_CREDS, data=json.dumps({"id_token": creds["id_token"].decode()}), headers={"Authorization": creds["id_token"].decode()})
        

        result = r.json()
        
        if result.get("message") == 'The incoming token has expired':
            return response.json({"error": True, "sucess": False, "message": "The id token has expired, Please login again", "data": None}, status=401)

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



    @aiomisc.threaded_separate
    def encrypt_file(self, in_filename_path, out_filename_path, iv, original_size, target_directory, chunksize=16*1024):
                
        with open(in_filename_path, 'rb') as infile:
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)

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

        return 

    @aiomisc.threaded_separate
    def put_file(self,  iv, upload_filename_path, unencrypted_file_size, backup_name, datasource_name):
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

        filename = os.path.basename(upload_filename_path)
        key_name = f"{self.identity_id}/{backup_name}/{datasource_name}/{filename}"

        metadata = {
            'x-amz-iv':  binascii.hexlify(iv).decode(),
            'x-amz-cek-alg': 'AES/CBC/PKCS5Padding',
            'x-amz-unencrypted-content-length': str(unencrypted_file_size)
        }

        s3client = boto3.client('s3')
        s3transfer = boto3.s3.transfer.S3Transfer(s3client)
        s3transfer.upload_file(upload_filename_path, self.bucket_name, key_name, extra_args={'Metadata': metadata})
        return 



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