


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
import coloredlogs, verboselogs, logging
from errors_module.errors import MnemonicRequiredError
verboselogs.install()
coloredlogs.install()
from errors_module.errors import APIBadRequest, PathDoesntExists
logger = logging.getLogger(__file__)
from database_calls.credentials import get_credentials


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
    __channel_id__ = "BACKUP_PROGRESS"
    def __init__(self, config):
        # self.datapod_dir = datapod_dir
        # self.user_index = f""

        # ##the directory inside the datapod_dir with all the backups
        # self.backup_dir = os.path.join(datapod_dir, "backup")

        # ##the directory which will have all the data, parsed or unparsed
        # self.data_dir = os.path.join(datapod_dir, "userdata")

        # ##the file inside the datapod_dir which will have the encryption keys of 
        # ##the user
        # self.encryption_file_name = os.path.join(datapod_dir, "keys/encryption.key")
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


    async def send_sse_message(self, message):
        url = f"http://{self.config.HOST}:{self.config.PORT}/send"
        logger.info(f"Sending sse message {message} at url {url}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps({"message": message, "channel_id": self.__channel_id__})) as response:
                result =  await response.json()
        
        #r = requests.post(url, )

        logger.info(f"Result sse message {result}")

        if result["error"]:
            logger.error(result["message"])
            return 

        logger.success(result["message"])
        return 

    async def create(self, archival_name):
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
        if not os.listdir(self.raw_data_path):
            raise APIBadRequest("The directory whose backup needs to be made is empty")
        
        #temp = tempfile.NamedTemporaryFile('wb', suffix='.tar.lzma', delete=False)
        temp = tempfile.NamedTemporaryFile('wb', suffix='.tar.gz', delete=False)
        #temp = tempfile.TemporaryFile()
        backup_path_dir = f"{self.backup_path}/{archival_name}"
        if not os.path.exists(backup_path_dir):
            os.makedirs(backup_path_dir)
        
        # backup_path = f"{self.backup_path}/{archival_name}/backup.tar.lzma"

            
        logging.info(f"The dir whose backup will be made {self.raw_data_path}")
        # logging.info(f"The dir where backup will be made {backup_path}")
        logging.error(f"Temporary file location is {temp.name}")

        if platform.system() == "Linux":
            backup_command = f"tar  --create  --gzip --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {self.raw_data_path}"                                                                                                                                                                                                                                            
            #backup_command = f"tar  --create  --lzma --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {self.raw_data_path}"                                                                                                                                                                                                                                            

        elif platform.system() == "Darwin":
            backup_command = f"gtar  --create  --lzma --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {self.raw_data_path}"
        else:
            raise APIBadRequest("The platform is not available for this os distribution")

        #backup_command = f"tar --create  --verbose --listed-incremental={self.user_index} --lzma {backup_path} {self.raw_data_path}"

        for out in self.config.OS_COMMAND_OUTPUT(backup_command, "Backup"):
            await self.send_sse_message(f"Archiving {out.split('/')[-1]}")
            
        async for msg in self.split(backup_path_dir, temp.name):
            await self.send_sse_message(msg)
        
        await self.send_sse_message(f"Removing Temporary file {temp.name}")
        
        self.remove_temporary_archive(temp.name)
        await self.send_sse_message(f"Temporary file {temp.name} Removed")

    

        return 

    def remove_temporary_archive(self, file_name):
        logging.warning(f"Removing temporary backup file {file_name}")
        try:
            os.remove(file_name)
        except Exception as e:
            logging.info(f"couldnt remove temporary archive file {file_name}")
        return 

    async def split(self, backup_path_dir, file_path):
        ##TODO: filename in split command is fixed but it may change on the type of compression being used
        dir_name, file_name = os.path.split(file_path)

        with cd(backup_path_dir):
            logging.info(f"THe directory where split is taking place {backup_path_dir}")
            if platform.system() == "Linux":
                #command = "tar --tape-length=%s -cMv  --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.config.TAR_SPLIT_SIZE, dir_name, file_name)
                command = "split --bytes=%sMB %s backup.tar.gz.1"%(self.config.TAR_SPLIT_SIZE, file_path)
            elif platform.system() == "Darwin":
                command = "split -b %sm %s backup.tar.gz.1"%(self.config.TAR_SPLIT_SIZE, file_path)
                
                #command = "gtar --tape-length=%s -cMv --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.config.TAR_SPLIT_SIZE, dir_name, file_name)
            else:
                raise APIBadRequest("The platform is not available for this os distribution")

            logging.warning(f"Splitting command is {command}")
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


    async def __init__(self, config, id_token):
        self.config = config
        self.id_token = id_token
        self.credentials = get_credentials(config.CREDENTIALS_TBL)
        self.encryption_key_file = tempfile.NamedTemporaryFile('wb', suffix='.txt', delete=False)
        logger.error(self.encryption_key_file.name)

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
        for out in self.config.OS_COMMAND_OUTPUT(sync_command, "Files are in Sync"):
            await send_sse_message(self.config, "BACKUP_PROGRESS", f"Upload to Cloud {out}")
        
        await send_sse_message(self.config, "BACKUP_PROGRESS", "Backup upload completed")

        return


    async def aws_temp_creds(self):

        r = requests.post(self.config.AWS_CREDS, data=json.dumps({
                        "id_token": self.id_token}))
        
        result = r.json()
        if result.get("error"):
            logger.error(result["message"])
            raise APIBadRequest(result["message"])
        
        return result["data"]["identity_id"], result["data"]["access_key"], result["data"]["secret_key"], result["data"]["session_token"]




async def send_sse_message(config, channel_id, message):
    url = f"http://{config.HOST}:{config.PORT}/send"
    logger.info(f"Sending sse message {message} at url {url}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json.dumps({"message": message, "channel_id": channel_id})) as response:
            result =  await response.json()
    
    #r = requests.post(url, )

    logger.info(f"Result sse message {result}")

    if result["error"]:
        logger.error(result["message"])
        return 

    logger.success(result["message"])
    return 




