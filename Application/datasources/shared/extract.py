
import aiomisc
import os
import zipfile
import tempfile



@aiomisc.threaded_separate
def extract(src_path: str, dest_path: str) -> str:
    """
    src_path : where the user has downloaded their ZIP file, 
    dest_path: where user has selecetd to keep their datapod data


    """
    temp_directory  =  tempfile.TemporaryDirectory()
    
    
    if not os.path.exists(src_path):
        raise APIBadRequest("This path doesnt exists")

    try:
        the_zip_file = zipfile.ZipFile(request.json["path"])
    except:
        raise APIBadRequest("Invalid zip file")


    logger.info(f"Testing zip {request.json['path']} file")
    ret = the_zip_file.testzip()

    if ret is not None:
        raise APIBadRequest("Invalid zip takeout file")



    try:
        shutil.unpack_archive(request.json["path"], extract_dir=temp_directory, format=None)
    except:
        raise APIBadRequest("Invalid zip facebook file")



def remove_temporary_archive(self, file_name):
    logger.warning(f"Removing temporary backup file {file_name}")
    try:
        os.removedirs(file_name)
    except Exception as e:
        logger.info(f"couldnt remove temporary archive file {file_name} with error {e}")
    return