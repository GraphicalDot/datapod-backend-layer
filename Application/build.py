
import os
import platform
import subprocess
from loguru import logger
import shutil
def os_command_output(command:str, final_message:str) -> str:
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        line = process.stdout.readline()
        if not line:
            logger.success(final_message)
            break
        yield line.decode().split("\r")[0]



def build_app():

    if platform.system() == "Linux":
        logger.info("Removing build directory")
        shutil.rmtree("build")
        backup_command = f"pyi-makespec --hidden-import _strptime --additional-hooks-dir pyinstaller_hooks --onefile --console --name Datapod --icon datapod.ico application.py"
        
        for out in os_command_output(backup_command, "Making Spec file completed"):
            logger.info(out)                                                                                                                                                                                                                                            
        #backup_command = f"tar  --create  --lzma --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {self.raw_data_path}"                                                                                                                                                                                                                                            
        command = "pyinstaller Datapod.spec"
        for out in os_command_output(command, "Build Complete"):
            logger.info(out)                                                                                                                                                                                                                                            

    elif platform.system() == "Darwin":
        pass
        #backup_command = f"gtar  --create  --lzma --no-check-device --verbose --listed-incremental={self.user_index} -f {temp.name} {self.raw_data_path}"
    else:
        raise Exception("The platform is not available for this os distribution")


if __name__ == "__main__":
    build_app()
    