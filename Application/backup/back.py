


from abc import ABC,abstractmethod 
import os
import subprocess
import time
import datetime
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
from LoginModule.login import login, aws_temp_creds



def os_system(command:str, final_message:str) -> str:
    """
    final message, This will be printed if there is no output on sttout on the 
    command line 

    """
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        line = process.stdout.readline()
        if not line:
            logging.info(final_message)
            break
        yield line.decode().split("\r")[0]

def run_command(command: str) -> None:

    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    # Read stdout from subprocess until the buffer is empty !
    
    for line in iter(p.stdout.readline, b''):
        if line: # Don't print blank lines
            yield line
    # This ensures the process has completed, AND sets the 'returncode' attr
    while p.poll() is None:                                                                                                                                        
        time.sleep(.1) #Don't waste CPU-cycles
    # Empty STDERR buffer
    err = p.stderr.read()
    if p.returncode != 0:
       # The run_command() function is responsible for logging STDERR 
       print("Error: " + str(err))
    return 


class Backup(ABC):

    def __init__(self, datapod_dir):
        self.datapod_dir = datapod_dir
        self.user_index = f""

        ##the directory inside the datapod_dir with all the backups
        self.backup_dir = os.path.join(datapod_dir, "backup")

        ##the directory which will have all the data, parsed or unparsed
        self.data_dir = os.path.join(datapod_dir, "userdata")

        ##the file inside the datapod_dir which will have the encryption keys of 
        ##the user
        self.encryption_file_name = os.path.join(datapod_dir, "keys/encryption.key")

    
    @abstractmethod
    def create(self):
        """


        """
        pass

    @abstractmethod
    def split(self):
        """
        if the backup is huge please split it into different 1GB files, so it will be easier to 
        sync on remote backup
        """
        pass

    @abstractmethod
    def sync_backup(self):
        """
        """
        pass



class S3Backup(Backup):

    def __init__(self, *args, **kwargs):
        Backup.__init__(self, *args, **kwargs)
        self.bucket_name = bucket_name


    def create(self):
                
        archival_name = datetime.datetime.utcnow().strftime("%B-%d-%Y")
        backup_command = f"tar cvpf {self.backup_dir}/{archival_name} --listed-incremental=usr.index --lzma {self.data_dir}"

        print (backup_command)
        for out in os_system(backup_command, "Backup"):
            logging.info(out)

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

    def split(self, tar_file_name):
        """
        if the backup is huge please split it into different 1GB files, so it will be easier to 
        sync on remote backup
        """
        command = f'split -b 1024M {tar_file_name} "{tar_file_name}.part."'

        pass


if __name__ == "__main__":
    pass





