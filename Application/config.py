
import os
import pathlib
p = str(pathlib.Path(os.getcwd()))
home = os.path.expanduser("~")

datapod_dir = os.path.join(home, ".Datapod")


keys_dir = os.path.join(datapod_dir, "Keys")


user_data_path = os.path.join(datapod_dir, "data")


db_dir_path = os.path.join(datapod_dir, "database")
#db_dir_path = "/home/feynman/Desktop/database"
archive_path = os.path.join(datapod_dir, "archive")


HOST = "localhost"
PORT = 8000
DEBUG = True