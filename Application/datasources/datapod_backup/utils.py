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
from asyncinit import asyncinit
from errors_module.errors import MnemonicRequiredError
from errors_module.errors import APIBadRequest, PathDoesntExists
from loguru import logger
from .variables import DATASOURCE_NAME
from .db_calls import get_credentials

##imported from another major module
from ..datapod_users.variables import DATASOURCE_NAME as USER_DATASOURCE_NAME

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)






class Backup(object):
    def __init__(self, config):

        self.config = config
        self.userdata_path = self.config.USERDATA_PATH
        
        ##file which keeps tracks of the data that has been backup last time
        self.user_index = self.config.USER_INDEX


        ##subdirectories in userdata path which deals with raw, parsed and database path 
        ##for the userdata.
        self.parsed_data_path = self.config.PARSED_DATA_PATH
        
        
        #self.raw_data_path = os.path.join(self.config.RAW_DATA_PATH, "facebook")
        self.raw_data_path = self.config.RAW_DATA_PATH

        self.db_path = self.config.DB_PATH
        self.backup_path = self.config.BACKUP_PATH

        self.num = 1

    async def send_sse_message(self, message):
        res = {"message": message, "percentage": self.num}
        if self.num < 80:
            await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
            self.num += 1
        # url = f"http://{self.config.HOST}:{self.config.PORT}/send"
        # logger.info(f"Sending sse message {message} at url {url}")
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url, data=json.dumps({"message": message, "channel_id": self.__channel_id__})) as response:
        #         result =  await response.json()
        
        # #r = requests.post(url, )


        # if result["error"]:
        #     logger.error(result["message"])
        #     return 

        # logger.success(result["message"])
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
        for datasource_name in datasources:
            dst_path = os.path.join(self.backup_path, archival_name, datasource_name) 
            src_path = os.path.join(self.raw_data_path, datasource_name )
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)
            await self.create(src_path, dst_path, datasource_name)
        return 

    async def create(self, src_path, dst_path, datasource_name): 

        #temp = tempfile.NamedTemporaryFile('wb', suffix='.tar.lzma', delete=False)
        temp = tempfile.NamedTemporaryFile('wb', suffix='.tar.gz', delete=False)
        #temp = tempfile.TemporaryFile()

        
        # backup_path = f"{self.backup_path}/{archival_name}/backup.tar.lzma"

            
        logger.debug(f"The dir whose backup will be made {src_path}")
        logger.debug(f"Temporary file location is {temp.name}")

        if platform.system() == "Linux":
            backup_command = f"tar  --create  --gzip --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {src_path}"                                                                                                                                                                                                                                            
            #backup_command = f"tar  --create  --lzma --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {self.raw_data_path}"                                                                                                                                                                                                                                            

        elif platform.system() == "Darwin":
            backup_command = f"gtar  --create  --lzma --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {src_path}"
        else:
            raise APIBadRequest("The platform is not available for this os distribution")

        #backup_command = f"tar --create  --verbose --listed-incremental={self.user_index} --lzma {backup_path} {self.raw_data_path}"
        initial_time = int(time.time())
        next_time = initial_time+15

        for out in self.config.OS_COMMAND_OUTPUT(backup_command, "Backup"):
            if int(time.time()) >= next_time:
                await self.send_sse_message(f"Archiving {out.split('/')[-1]} for {datasource_name}")
                next_time += 10

        async for msg in self.split(dst_path, temp.name):
            await self.send_sse_message(msg)
        
        await self.send_sse_message(f"Removing Temporary file {temp.name}")
        
        self.remove_temporary_archive(temp.name)
        await self.send_sse_message(f"Temporary file {temp.name} Removed")

    

        return 

    def remove_temporary_archive(self, file_name):
        logger.warning(f"Removing temporary backup file {file_name}")
        try:
            os.remove(file_name)
        except Exception as e:
            logger.info(f"couldnt remove temporary archive file {file_name} with error {e}")
        return 

    async def split(self, dst_path, file_path):
        ##TODO: filename in split command is fixed but it may change on the type of compression being used
        dir_name, file_name = os.path.split(file_path)

        with cd(dst_path):
            logger.info(f"THe directory where split is taking place {dst_path}")
            if platform.system() == "Linux":
                #command = "tar --tape-length=%s -cMv  --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.config.TAR_SPLIT_SIZE, dir_name, file_name)
                command = "split --bytes=%sMB %s backup.tar.gz.1"%(self.config.TAR_SPLIT_SIZE, file_path)
            elif platform.system() == "Darwin":
                command = "split -b %sm %s backup.tar.gz.1"%(self.config.TAR_SPLIT_SIZE, file_path)
                
                #command = "gtar --tape-length=%s -cMv --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.config.TAR_SPLIT_SIZE, dir_name, file_name)
            else:
                raise APIBadRequest("The platform is not available for this os distribution")

            logger.warning(f"Splitting command is {command}")
            for out in self.config.OS_COMMAND_OUTPUT(command, "Split"):
                yield (f"Archiving {out[-70:]}")

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
        self.config = config
        #self.credentials = get_credentials(config.CREDENTIALS_TBL)
        self.encryption_key_file = tempfile.NamedTemporaryFile('wb', suffix='.txt', delete=False)
        logger.error(self.encryption_key_file.name)
        self.credentials = await get_credentials(self.config[USER_DATASOURCE_NAME]["tables"]["creds_table"])
        if not self.credentials:
            raise APIBadRequest("User is not logged in")
        
        self.credentials = list(self.credentials)[0]
        ##in this temporary file, private key is now written
        logger.info(self.credentials)

        if not self.credentials["encryption_key"]:
            raise MnemonicRequiredError()

        with open(self.encryption_key_file.name, "wb") as f:
            f.write(binascii.unhexlify(self.credentials["encryption_key"].encode()))



        self.identity_id, self.access_key, self.secret_key, self.session_token =  await self.aws_temp_creds()
        
        logger.info(f"Access key for AWS <<{self.access_key}>>")
        logger.info(f"Secret key for AWS <<{self.secret_key}>>")
        logger.info(f"Session Token  for AWS <<{self.session_token}>>")
        # async for msg in S3Backup.sync_backup(request.app.config, identity_id, access_key, secret_key, session_token):
        #     logger.info(msg)

        os.environ['AWS_ACCESS_KEY_ID'] = self.access_key # visible in this process + all children
        os.environ['AWS_SECRET_ACCESS_KEY'] = self.secret_key # visible in this process + all children
        os.environ['AWS_SESSION_TOKEN'] = self.session_token # visible in this process + all children
        os.environ["AWS_DEFAULT_REGION"] = self.config.AWS_S3["default_region"]

    async def check_size(self):
        size_command = f"aws s3 ls --recursive --human-readable --summarize s3://{self.config.AWS_S3['bucket_name']}/{self.identity_id}"
        logger.info(size_command)

        for out in self.config.OS_COMMAND_OUTPUT(size_command, "Files are in Sync"):
            logger.info(out)
        return


    async def sync_backup(self):


        # _key = generate_aes_key(32)

        # key = "".join(map(chr, _key))
        # print (key)
        # encryption_key_path = "/home/feynman/.Datapod/Keys/encryption.key"
        configure_command = "aws configure set default.s3.max_bandwidth 15MB/s"
        for out in self.config.OS_COMMAND_OUTPUT(configure_command, "Limit upload speed"):
            logger.info (out)

        sync_command = f"aws s3 sync --sse-c AES256 --sse-c-key fileb://{self.encryption_key_file.name} {self.config.BACKUP_PATH} s3://{self.config.AWS_S3['bucket_name']}/{self.identity_id}"
        print (sync_command)

        num = 0
        for out in self.config.OS_COMMAND_OUTPUT(sync_command, "Files are in Sync"):
            res = {"message": "BACKUP_PROGRESS", "percentage": num}
            await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
            num += 1


        return


    async def aws_temp_creds(self):

        # r = requests.post(self.config.AWS_CREDS, data=json.dumps({
        #                 "id_token": self.id_token}))
        
        # result = r.json()
        # if result.get("error"):
        #     logger.error(result["message"])
        #     raise APIBadRequest(result["message"])
        
        # return result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]

        creds = await get_credentials(self.config[USER_DATASOURCE_NAME]["tables"]["creds_table"])


        if not creds:
            raise APIBadRequest("User is not logged in")
        
        creds = list(creds)[0]
        r = requests.post(self.config.LOGIN, data=json.dumps({"username": creds["username"], "password": creds["password"]}))
    
        result = r.json()
        if result.get("error"):
            logger.error(result["message"])
            raise APIBadRequest(result["message"])
        
        logger.debug(result)
        r = requests.post(self.config.TEMPORARY_S3_CREDS, data=json.dumps({"id_token": result["data"]["id_token"]}), headers={"Authorization": result["data"]["id_token"]})

        result = r.json()
        logger.debug(result)
        if result.get("error"):
            logger.error(result["message"])
            raise APIBadRequest(result["message"])
        return result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]




