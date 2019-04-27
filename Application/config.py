
import os
import pathlib
p = str(pathlib.Path(os.getcwd()))
user_data = os.path.join(str(p), "userdata")
db_data = os.path.join(str(p), "database")
HOST = "localhost"
PORT = 8000
DEBUG = True