
import aiomisc
import os
import zipfile
import tempfile
from errors_module.errors import APIBadRequest
from loguru import logger
import shutil
import hashlib as hash
from typing import Any, Dict, Tuple, Callable
import datetime
# from memory_profiler import profile


# @profile
@aiomisc.threaded_separate
def extract(src_path: str, dst_path_prefix: str, config: Dict[str, Any], datasource_name: str, username: str) -> Tuple[str, str]:
    """
    src_path : where the user has downloaded their ZIP file, 

    temp_directory  =  tempfile.TemporaryDirectory()

    """
    # temp_directory = tempfile.mkdtemp()
    logger.info("Entered into the extract function")
    if not os.path.exists(src_path):
        raise APIBadRequest("This path doesnt exists")

    # try:
    #     the_zip_file = zipfile.ZipFile(src_path)
    # except:
    #     raise APIBadRequest("Invalid zip file")


    # logger.info(f"Testing zip {src_path} file")
    # ret = the_zip_file.testzip()

    # if ret is not None:
    #     raise APIBadRequest(f"Invalid zip datasource_name file")


    _checksum = checksum(src_path)
    
    archives_present = get_archives(config[datasource_name]["tables"]["archives_table"], _checksum)
    
    if archives_present:
        raise APIBadRequest("Zip file already have been uploaded")
        


    utc_timestamp = datetime.datetime.utcnow().strftime("%d-%m-%Y")
    dst_path_suffix = f"{utc_timestamp}-{_checksum}"

    logger.info(f"This is the new destination suffix {dst_path_suffix}")
    
    dst_path =  os.path.join(dst_path_prefix, username, dst_path_suffix)


    try:
        with zipfile.ZipFile(src_path) as zf:
            zf.extractall(dst_path)
        #shutil.unpack_archive(src_path, extract_dir=dst_path, format=None)
    except MemoryError:
        logger.error(f"We ran out of memory while processing {datasource_name}, Please try again")
        raise Exception(f"We ran out of memory while processing {datasource_name}, Please try again")
    except:

        raise APIBadRequest(f"Invalid zip {datasource_name} file")

    logger.info(f"Setting new archival for {datasource_name} ")
    set_archives(config[datasource_name]["tables"]["archives_table"], dst_path, username, _checksum)
    logger.info(f"This is the dst_path for {datasource_name} is {dst_path}")
    
    return _checksum, dst_path





# @profile
@aiomisc.threaded_separate
def extract(src_path: str, dst_path_prefix: str, config: Dict[str, Any], datasource_name: str, username: str) -> Tuple[str, str]:
    """
    src_path : where the user has downloaded their ZIP file, 

    temp_directory  =  tempfile.TemporaryDirectory()

    """
    # temp_directory = tempfile.mkdtemp()
    logger.info("Entered into the extract function")
    if not os.path.exists(src_path):
        raise APIBadRequest("This path doesnt exists")



    _checksum = checksum(src_path)
    
    archives_present = get_archives(config[datasource_name]["tables"]["archives_table"], _checksum)
    
    if archives_present:
        raise APIBadRequest("Zip file already have been uploaded")
        


    utc_timestamp = datetime.datetime.utcnow().strftime("%d-%m-%Y")
    dst_path_suffix = f"{utc_timestamp}-{_checksum}"

    logger.info(f"This is the new destination suffix {dst_path_suffix}")
    
    dst_path =  os.path.join(dst_path_prefix, username, dst_path_suffix)


    if src_path.endswith(".mbox"):
        logger.debug("This is a bare Mbox file from Google takeout")
        mail_path =  os.path.join(dst_path, "Takeout/Mail")
        os.makedirs(mail_path)
        shutil.copy(src_path, mail_path)
    else:

        try:
            with zipfile.ZipFile(src_path) as zf:
                zf.extractall(dst_path)
            #shutil.unpack_archive(src_path, extract_dir=dst_path, format=None)
        except MemoryError:
            logger.error(f"We ran out of memory while processing {datasource_name}, Please try again")
            raise Exception(f"We ran out of memory while processing {datasource_name}, Please try again")
        except:

            raise APIBadRequest(f"Invalid zip {datasource_name} file")

    logger.info(f"Setting new archival for {datasource_name} ")
    set_archives(config[datasource_name]["tables"]["archives_table"], dst_path, username, _checksum)
    logger.info(f"This is the dst_path for {datasource_name} is {dst_path}")
    
    return _checksum, dst_path




def remove_temporary_archive(self, file_name):
    logger.warning(f"Removing temporary backup file {file_name}")
    try:
        os.removedirs(file_name)
    except Exception as e:
        logger.info(f"couldnt remove temporary archive file {file_name} with error {e}")
    return




def get_archives(archives_table, checksum):
    try:
        archives_table\
            .select()\
            .where(archives_table.checksum==checksum).get()
        return True
    except Exception as e:
        logger.info(f"Archieve couldnt be found {e}")

        return False
    return 




def set_archives(archives_table, path, username, checksum):
    try:
        archives_table\
            .insert(
                path= path, 
                username= username,
                checksum=checksum
            )\
            .execute()
    except Exception as e:
        logger.info(f"Archive insertion couldnt be found {e}")

        return False
    return 


def checksum(src_path: str) -> str:


    # Specify how many bytes of the file you want to open at a time
    BLOCKSIZE = 65536

    sha = hash.sha256()
    with open(src_path, 'rb') as kali_file:
        file_buffer = kali_file.read(BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = kali_file.read(BLOCKSIZE)
            
    return sha.hexdigest()

