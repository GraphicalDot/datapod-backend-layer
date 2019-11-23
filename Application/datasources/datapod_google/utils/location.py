import pytz
import datetime
import hashlib
import json
import os
import pytz
import asyncio
import concurrent
import asyncinit
from collections import Counter
import operator
from geopy.geocoders import Nominatim
from loguru import logger
from ..variables import DATASOURCE_NAME

from ..db_calls import store_locations, store_locations_approximate



def month_aware_time_stamp(naive_timestamp=None): 
     tz_kolkata = pytz.timezone('Asia/Kolkata') 
     time_format = "%Y-%m-%d %H:%M:%S" 
     if naive_timestamp: 
         aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp)) 
     else: 
         naive_timestamp = datetime.datetime.now() 
         aware_timestamp = tz_kolkata.localize(naive_timestamp) 
     return (aware_timestamp.strftime(time_format + " %Z%z"), aware_timestamp.year, aware_timestamp.month)



class Location(object):

    def __init__(self, time_stamp, latitude, longitude, accuracy, 
                velocity, heading, altitude, vertical_accuracy, activity):
        self.time_stamp = float(time_stamp)/1000
        self.latitude = float(latitude)/10000000
        self.longitude =  float(longitude)/10000000
        self.accuracy = accuracy
        self.velocity = velocity
        self.heading = heading
        self.altitude = altitude
        self.vertical_accuracy = vertical_accuracy
        self.activity = activity

        self.timestamp, self.year, self.month = month_aware_time_stamp(self.time_stamp)
        self.hash = self.__hash__()

    def data(self):
        return self.__dict__

    ##treat places similar if three places decimal matches
    def __hash__(self):
        latitude = str(self.latitude)[0:5] 
        longitude = str(self.longitude)[0:5] 
        return hash((latitude, longitude, self.year, self.month)) & ((1<<64)-1)


    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self.hash == other.hash 
        return False

    def __ne__(self, other):
        """Override the default Unequal behavior"""
        return self.hash != other.hash 


class LocationApproximate(object):
    
    def __init__(self, time_stamp, latitude, longitude, accuracy, 
                velocity, heading, altitude, vertical_accuracy, activity):
        self.time_stamp = float(time_stamp)/1000
        self.latitude =  "{0:.2f}".format(float(latitude)/10000000)   
        self.longitude = "{0:.2f}".format(float(longitude)/10000000)
        
        self._latitude =  float(latitude)/10000000   
        self._longitude = float(longitude)/10000000
        
        self.accuracy = accuracy
        self.velocity = velocity
        self.heading = heading
        self.altitude = altitude
        self.vertical_accuracy = vertical_accuracy
        self.activity = activity

        self.timestamp, self.year, self.month = month_aware_time_stamp(self.time_stamp)
        self.hash = self.__hash__()

    def data(self):
        return self.__dict__

    ##treat places similar if three places decimal matches
    def __hash__(self):
        latitude = str(self.latitude)[0:5] 
        longitude = str(self.longitude)[0:5] 
        return hash((latitude, longitude, self.year, self.month)) & ((1<<64)-1)


    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self.hash == other.hash 
        return False

    def __ne__(self, other):
        """Override the default Unequal behavior"""
        return self.hash != other.hash 


class LocationHistory(object):
    
    def __init__(self, config, dest_path, username, checksum):
        self.geolocator = Nominatim(user_agent="Datapod")
        self.username = username
        self.checksum = checksum
        self.config = config
        self.path = os.path.join(dest_path, "Takeout/Location History/Location History.json")
        self.pr_executor = concurrent.futures.ProcessPoolExecutor(max_workers=10)
        self.th_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.main_key = "location"
        self.location_db_data = {}
        self.location_signature = {} ##which will have details of what year has what all months
        if not os.path.exists(self.path):
            logger.error("Location data doesnt exists")


    def reverse_geo_code(self, lat, lon):
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}")
            result = location.raw["address"]
        except Exception as e:
            try:
                location = self.geolocator.reverse(f"{lat}, {lon}")
                result = location.raw["address"]
            except Exception as e:
                logger.error(e)
                result = None
        return result


    
    async def parse(self):
        with open(self.path, "rb") as fi:
            result  = fi.read() 
            location = json.loads(result)

        location_data = iter(location["locations"])
        #tasks = [self.reverse_geo_code(loc["latitudeE7"]/10000000, loc["longitudeE7"]/10000000) \
        #for loc in location_data]
    
        ##update the location history array with month and year
        final ={}
        for item in location_data: 
            i_tem = LocationApproximate(item["timestampMs"], item["latitudeE7"], item["longitudeE7"], item["accuracy"], 
                            item.get("velocity"), item.get("heading"), item.get("altitude"), 
                            item.get("vertical_accuracy"), item.get("activity"))
            
            final.setdefault(i_tem.hash, i_tem.data())

        logger.info(f"Data items in location final is {len(final.values())}")
        for item in iter(final.values()):
            data = { "tbl_object": self.config[DATASOURCE_NAME]["tables"]["location_approximate_table"],
                    "username": self.username,
                    "checksum": self.checksum,
                    "_latitude": item["_latitude"], "_longitude": item["_longitude"],
                    "time": item["time_stamp"], "latitude": item["latitude"], "longitude": item["longitude"],
                    "accuracy": item["accuracy"], "vertical_accuracy": item["vertical_accuracy"],
                    "velocity": item["velocity"], "heading": item["heading"], "altitude": item["altitude"],
                    "activity": item["activity"]

            }
            await store_locations_approximate(**data)

        #self.push_db(loc_data, int(_t["month"]), int(_t["year"]))
        #     if not self.location_db_data.get(i_tem.year):
        #         #if year is not present
        #         self.location_db_data[i_tem.year] = {i_tem.month: [i_tem]}
        #         self.location_signature[i_tem.year] = [i_tem.month]
        #     else:
        #         ##year is present
        #         if  i_tem.month not in self.location_signature[i_tem.year]:
        #             self.location_signature[i_tem.year] += [i_tem.month]

        #         if  not  self.location_db_data[i_tem.year].get(i_tem.month):
        #             #month is not present
        #             self.location_db_data[i_tem.year].update({i_tem.month: [i_tem]})
        #         else:
        #             #month is present
        #             self.location_db_data[i_tem.year][i_tem.month] += [i_tem]

        # print (self.location_signature)
        # self.store()
        # self.insert_location_signature()
        return 


    

    def most_visited_places(self, data):
        duplicates = Counter(data)
        _most_common =  [i[0].data() for i in duplicates.most_common(5)]
        for item in _most_common:
            address = self.reverse_geo_code(item["latitude"], item["longitude"])
            item.update({"address": address})
        return _most_common 


    def insert_location_signature(self):
        """
        To store all the data on the basis of the year and the month 
        """
        db_instance = create_db_instance(self.db_dir_path)
        insert_key("location", self.location_signature, db_instance)
        close_db_instance(db_instance)
        
if __name__ == "__main__":
    path = "/home/feynman/.datapod/userdata/raw/Google/houzier.saurav@gmail.com/19-11-2019-56c3eccc615e71f1e2fcd0d0b07220532947651bc13c0e0fdfa621a2a1783c35/Takeout"
