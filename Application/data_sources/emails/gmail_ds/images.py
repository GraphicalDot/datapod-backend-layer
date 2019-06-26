
SERVER = "imap.gmail.com"
import hashlib
from pprint import pprint
import datetime
import email
import imaplib
import mailbox
import os, sys
import base64
import re
from dateutil import parser
# path = os.path.dirname(os.path.realpath(os.getcwd()))
# print (path)
import datetime
# from  analysis.bank_statements import BankStatements
# from  analysis.cab_service import CabService
import bleach
import json

# import coloredlogs, verboselogs, logging
# verboselogs.install()
# coloredlogs.install()
# logger = logging.getLogger(__name__)
# from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, StoreInChunks
DEBUG=False
import time
from asyncinit import asyncinit
import pytz
import asyncio
import concurrent

import coloredlogs, verboselogs, logging
from geopy.geocoders import Nominatim
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

from utils.utils import timezone_timestamp



@asyncinit
class GoogleImages(object):
    __source__ = "takeout"
    def __init__(self, gmail_takeout_path, app_config):
        #self.db_dir_path = db_dir_path
        self.path = os.path.join(gmail_takeout_path, "Google Photos")
        #self.db_instance = create_db_instance(db_dir_path)
        self.app_config = app_config
        if not os.path.exists(self.path):
            raise Exception("Reservations and purchase data doesnt exists")
        self.images = []
        self.videos = []
        self.extras = []



    async def parse(self):
        for folder in os.listdir(google_photos_dir):
            folder_path = os.path.join(google_photos_dir, folder)
            if os.path.isdir(folder_path):
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file )
                    res = [file.endswith(ext) for ext in ["png", "PNG", "jpg", "JPG", "gif", "GIF"]]
                    if any(res):
                        #print (f"File is Image file {file} with {res}")
                        images.append(file_path)
                    elif any([file.endswith(ext) for ext in ["mp4", "mov", "MOV", "MP4"]]):
                        #print (f"File is Video file {file}")
                        videos.append(file_path)
                    else:
                        extras.append(file_path)
        return 

    def image_json_path(self, image_path):
        json_path = os.path.join(os.path.dirname(image_path), f"{os.path.abspath(image_path)}.json")
        if os.path.exists(json_path):
            return json_path
        return None


    def some(self):

        for image_path in images:
            json_path = os.path.join(os.path.dirname(image_path), f"{os.path.abspath(image_path)}.json")
            if os.path.exists(json_path):
                pass
            else:
                new_path = f'{".".join(image_path.split(".")[:-1])[0:-1]}.json'
                if not os.path.exists(new_path):
                    #print (image_path, new_path)
                    _new_path = f'{".".join(image_path.split(".")[:-1])}.json'
                    if not os.path.exists(_new_path):
                        print (image_path, _new_path)




    def parser3(self):
        for image_path in images:
    ...:     json_path = os.path.join(os.path.dirname(image_path), f"{os.path.abspath(image_path)}.json")
    ...:     if os.path.exists(json_path):
    ...:         with open(json_path, "rb") as fi:
    ...:             data = json.loads(fi.read())
    ...:             #pprint.pprint (data)
    ...:             print (f'creationtime == {datetime.datetime.utcfromtimestamp(int(data["creationTime"]["timestamp"]))}')
    ...:             print (f'modificationTime == {datetime.datetime.utcfromtimestamp(int(data["modificationTime"]["timestamp"]))}')
    ...:             print (f'photoTakenTime == {datetime.datetime.utcfromtimestamp(int(data["photoTakenTime"]["timestamp"]))}')
    ...:             print (f'descriptiotn == {data["description"]}')
    ...:             print (f'url == {data["url"]}')
    ...:             print (f'title == {data["title"]}')





