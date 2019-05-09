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
from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, StoreInChunks
import coloredlogs, verboselogs, logging
import operator
from geopy.geocoders import Nominatim
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)




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
        self.hash = self.hashed()

    def data(self):
        return self.__dict__

    def hashed(self):
        string = str(self.latitude)+str(self.longitude)
        return hashlib.sha3_224(string.encode()).hexdigest()

    ##treat places similar if three places decimal matches
    def __hash__(self):
        latitude = str(self.latitude)[0:6] 
        longitude = str(self.longitude)[0:6] 
        string = latitude+longitude 
        return hash(string.encode())


    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self.hash == other.hash and self.month == other.month and self.year == other.year
        return False

    def __ne__(self, other):
        """Override the default Unequal behavior"""
        return self.hash != other.hash or self.month != other.month or self.year != other.year

class LocationHistory(object):
    
    def __init__(self, gmail_takeout_path, db_dir_path):
        self.geolocator = Nominatim(user_agent="Datapod")
        self.db_dir_path = db_dir_path
        self.path = os.path.join(gmail_takeout_path, "Location History/Location History.json")
        self.pr_executor = concurrent.futures.ProcessPoolExecutor(max_workers=10)
        self.th_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.main_key = "location"
        self.location_db_data = {}
        if not os.path.exists(self.path):
            raise Exception("Reservations and purchase data doesnt exists")


    def reverse_geo_code(self, lat, lon):
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}")
            result = location.raw["address"]
        except Exception as e:
            try:
                location = self.geolocator.reverse(f"{lat}, {lon}")
                result = location.raw["address"]
            except Exception as e:
                logging.error(e)
                result = None
        return result


    def format(self):
        #self.db_instance = create_db_instance(self.db_dir_path)
        with open(self.path, "rb") as fi:
            result  = fi.read() 
            location = json.loads(result)

        location_data = location["locations"]
        #tasks = [self.reverse_geo_code(loc["latitudeE7"]/10000000, loc["longitudeE7"]/10000000) \
        #for loc in location_data]
    
        ##update the location history array with month and year
        for item in location_data: 
            i_tem = Location(item["timestampMs"], item["latitudeE7"], item["longitudeE7"], item["accuracy"], 
                            item.get("velocity"), item.get("heading"), item.get("altitude"), 
                            item.get("vertical_accuracy"), item.get("activity"))
            
            #self.push_db(loc_data, int(_t["month"]), int(_t["year"]))
            if not self.location_db_data.get(i_tem.year):
                #if year is not present
                self.location_db_data[i_tem.year] = {i_tem.month: [i_tem]}
            else:
                ##year is present
                if  not  self.location_db_data[i_tem.year].get(i_tem.month):
                    #month is not present
                    self.location_db_data[i_tem.year].update({i_tem.month: [i_tem]})
                else:
                    #month is present
                    self.location_db_data[i_tem.year][i_tem.month] += [i_tem]

        for year in self.location_db_data.keys():
            for month in self.location_db_data[year].keys():
                res = self.location_db_data[year][month]    
                logger.info(f"Year {year} and Month {month}, number of locations visited is {len(res)} ")
        #insert_key(self.main_key, self.location_db_data, self.db_instance)
        #close_db_instance(self.db_instance)

        print (self.most_visited_places(self.location_db_data))
        return 


    def most_visited_places(self, data):
        most_visited = {}
        for year in data.keys():
            for month in data[year].keys():
                res = data[year][month]
                
                ##will make a dictionary out of the list with values as their number
                ##of duplicacy
                duplicates = Counter(res)
                _most_common =  [i[0].data() for i in duplicates.most_common(3)]
                logger.info(_most_common)
                for item in _most_common:
                    address = self.reverse_geo_code(item["latitude"], item["longitude"])
                    item.update({"address": address})

                if most_visited.get(year):
                    most_visited[year].update({month: _most_common})
                else:
                    most_visited.update({year: {month: _most_common}})


        return most_visited        


    def push_db(self, data, month, year):
        """
        {'timestampMs': '1510211478168', 'latitudeE7': 285594542, 'longitudeE7': 772102843, 'accuracy': 1414, 'altitude': 78,
        'verticalAccuracy': 192, 'timestamp': '2017-11-09 12:41:18 IST+0530', 'year': 2017, 'month': 11}
        """
        if not self.location_db_data.get(year):
            self.location_db_data[year] = [month]
        else:
            if month not in self.location_db_data[year]:
                months = self.location_db_data[year]
                months.append(month)
                self.location_db_data[year] = months

        key = f'location_{year}_{month}'
        logging.info(key)
        stored_value = get_key(key, self.db_instance)

        value = [data]
        if stored_value:
            value = value+stored_value  


        insert_key(key, value, self.db_instance)
        return 

    async def parse(self):



        tasks = [asyncio.get_event_loop().run_in_executor(
                                self.th_executor, 
                                self.reverse_geo_code, 
                                loc["latitudeE7"]/10000000, 
                                loc["longitudeE7"]/10000000) for loc in location_data[0:1000]]
        #several_futures = asyncio.gather(*tasks)
        #results = loop.run_until_complete(several_futures)
        completed, pending = await asyncio.wait(tasks)
        results = [t.result() for t in completed]
        #results = await asyncio.gather(*tasks)
        #await asyncio.wait(tasks)
        #loop.run_until_complete(asyncio.wait(tasks))
        return results 

