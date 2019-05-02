
import os
import pathlib
p = str(pathlib.Path(os.getcwd()))
user_data_path = os.path.join(str(p), "userdata")
db_dir_path = os.path.join(str(p), "database")
archive_path = os.path.join(str(p), "archive")


HOST = "localhost"
PORT = 8000
DEBUG = True