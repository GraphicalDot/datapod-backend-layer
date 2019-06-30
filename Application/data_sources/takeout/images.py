#-*- coding: utf-8 -*-
import os
import json
from pprint import pprint
from asyncinit import asyncinit
import datetime 

@asyncinit
class ParseGoogleImages(object):
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
        self.images_data = []


    async def parse(self):
        await self.filter_images()
        for (image_path, image_json_path) in self.images:
            res = await self.image_data(image_path, image_json_path)
            self.images_data.append(res)
        return 

    async def filter_images(self):
        for folder in os.listdir(self.path):
            folder_path = os.path.join(self.path, folder)
            if os.path.isdir(folder_path):
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file )
                    res = [file.endswith(ext) for ext in ["png", "PNG", "jpg", "JPG", "gif", "GIF"]]
                    if any(res):
                        #print (f"File is Image file {file} with {res}")
                        img_json = await self.find_image_json(file_path)
                        if img_json:
                            self.images.append((file_path, img_json))
                    elif any([file.endswith(ext) for ext in ["mp4", "mov", "MOV", "MP4"]]):
                        self.videos.append(file_path)
                    else:
                        pass
        return

    def image_json_path(self, image_path):
        json_path = os.path.join(os.path.dirname(image_path), f"{os.path.abspath(image_path)}.json")
        if os.path.exists(json_path):
            return json_path
        return None


    async def find_image_json(self, image_path):
        """ 
        Heuristics to find json file of the corresponding image, the json is usually
        located in the same folder as the image, 
        """

        json_path = os.path.join(os.path.dirname(image_path), f"{os.path.abspath(image_path)}.json")
        if os.path.exists(json_path):
            return json_path
        else:
            new_path = f'{".".join(image_path.split(".")[:-1])[0:-1]}.json'
            if os.path.exists(new_path):
                return new_path
                _new_path = f'{".".join(image_path.split(".")[:-1])}.json'
                if os.path.exists(_new_path):
                   return _new_path
        return None



    async def image_data(self, image_path, image_json_path):
        with open(image_json_path, "rb") as fi:
            data = json.loads(fi.read())
            #pprint (data)
            res = {'creation_time': datetime.datetime.utcfromtimestamp(int(data["creationTime"]["timestamp"])), 
                    'modification_time' : datetime.datetime.utcfromtimestamp(int(data["modificationTime"]["timestamp"])),
                    'photo_taken_time':  datetime.datetime.utcfromtimestamp(int(data["photoTakenTime"]["timestamp"])),
                    'description': data["description"],
                    'url': data["url"],
                    'title': data["title"],
                     'geo_data':  data["geoData"],
                    'image_path': image_path,
                    "source": self.__source__
            }
            return res
