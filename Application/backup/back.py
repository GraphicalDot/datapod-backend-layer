


from abc import ABC,abstractmethod 
import os
import subprocess
import time
import datetime
import platform
import tempfile

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
from errors_module.errors import APIBadRequest, PathDoesntExists
logger = logging.getLogger(__file__)



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

    def __init__(self, request):
        # self.datapod_dir = datapod_dir
        # self.user_index = f""

        # ##the directory inside the datapod_dir with all the backups
        # self.backup_dir = os.path.join(datapod_dir, "backup")

        # ##the directory which will have all the data, parsed or unparsed
        # self.data_dir = os.path.join(datapod_dir, "userdata")

        # ##the file inside the datapod_dir which will have the encryption keys of 
        # ##the user
        # self.encryption_file_name = os.path.join(datapod_dir, "keys/encryption.key")
        self.request = request
        self.userdata_path = self.request.app.config.USERDATA_PATH
        
        ##file which keeps tracks of the data that has been backup last time
        self.user_index = self.request.app.config.USER_INDEX


        ##subdirectories in userdata path which deals with raw, parsed and database path 
        ##for the userdata.
        self.parsed_data_path = self.request.app.config.PARSED_DATA_PATH
        
        
        #self.raw_data_path = os.path.join(self.request.app.config.RAW_DATA_PATH, "facebook")
        self.raw_data_path = self.request.app.config.RAW_DATA_PATH

        self.db_path = self.request.app.config.DB_PATH
        self.backup_path = self.request.app.config.BACKUP_PATH


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

        for out in self.request.app.config.OS_COMMAND_OUTPUT(backup_command, "Backup"):
            yield (f"Archiving {out.split('/')[-1]}")
            
        async for msg in self.split(backup_path_dir, temp.name):
            yield msg
        
        self.remove_temporary_archive(temp.name)
    
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
                #command = "tar --tape-length=%s -cMv  --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.request.app.config.TAR_SPLIT_SIZE, dir_name, file_name)
                command = "split --bytes=%sMB %s backup.tar.gz.1"%(self.request.app.config.TAR_SPLIT_SIZE, file_path)
            elif platform.system() == "Darwin":
                command = "split -b %sm %s backup.tar.gz.1"%(self.request.app.config.TAR_SPLIT_SIZE, file_path)
                
                #command = "gtar --tape-length=%s -cMv --file=tar_archive.{tar,tar-{2..1000}}  -C %s %s"%(self.request.app.config.TAR_SPLIT_SIZE, dir_name, file_name)
            else:
                raise APIBadRequest("The platform is not available for this os distribution")

            logging.warning(f"Splitting command is {command}")
            for out in self.request.app.config.OS_COMMAND_OUTPUT(command, "Split"):
                yield (f"Archiving {out[-70:]}")

            for name in os.listdir("."):
                logger.info(f"Creating sha checksum for backup split file {name}")
                for out in self.request.app.config.OS_COMMAND_OUTPUT(f"sha512sum {name} > {name}.sha512", "sha checksum"):
                    yield (f"Creating sha checksum {out}")
        
            ##calculating the whole backup file tar 
            for out in self.request.app.config.OS_COMMAND_OUTPUT(f"sha512sum {file_path} > backup.sha512", "sha checksum"):
                yield (f"Creating sha checksum {out}")

        return 




class S3Backup(Backup):

    def __init__(self, *args, **kwargs):
        Backup.__init__(self, *args, **kwargs)
        self.bucket_name = bucket_name


    
    def sync_backup(self, dir_path, identity_id, access_key, secret_key, default_region, session_token):
        if not os.path.exists(dir_path):
            raise Exception("Please provide a valid directory name")

        os.environ['AWS_ACCESS_KEY_ID'] = access_key # visible in this process + all children
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key # visible in this process + all children
        os.environ['AWS_SESSION_TOKEN'] = session_token # visible in this process + all children
        os.environ["AWS_DEFAULT_REGION"] = default_region

        # _key = generate_aes_key(32)

        # key = "".join(map(chr, _key))
        #print (key)
        encryption_key_path = "/home/feynman/.Datapod/Keys/encryption.key"

        sync_command = f"aws s3 sync --sse-c AES256 --sse-c-key fileb://{encryption_key_path} {dir_path} s3://{self.bucket_name}/{identity_id}"
        print (sync_command)
        for out in os_system(sync_command, "Files are in Sync"):
            logging.info(out)
        return 




if __name__ == "__main__":
    pass





