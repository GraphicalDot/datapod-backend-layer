
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
class PurchaseReservations(object):
    __source__ = "takeout"
    def __init__(self, gmail_takeout_path, app_config):
        #self.db_dir_path = db_dir_path
        self.path = os.path.join(gmail_takeout_path, "Purchases _ Reservations")
        #self.db_instance = create_db_instance(db_dir_path)
        self.app_config = app_config
        if not os.path.exists(self.path):
            logger.error("Reservations and purchase data doesnt exists")
            raise Exception("Reservations and purchase data doesnt exists")
        return


    async def parse(self):
        purchases = []
        reservations = []
        for filename in os.listdir(self.path):
            filepath = os.path.join(self.path, filename)
            with open(filepath, "r") as f: 
                data = json.loads(f.read()) 
                try: 
                    result = await self.parse_purchase(data)
                    result.update({"source": self.__source__})
                    if result.get("type") == "purchase":
                        result.pop("type")
                        result.pop('dest')
                        result.pop('src')

                        purchases.append(result)
                    else:
                        result.pop("type")
                        reservations.append(result)

                except Exception as e: 
                    logger.error(f"In DATA {data} error is  <<{e}>>, filename is {filepath}" )
        return reservations, purchases

    async def parse_purchase(self, data):
        
        src = None
        dest = None
        _type = None
        merchant_name = None
        products = []
        if data.get("transactionMerchant"):
            merchant_name = data["transactionMerchant"]["name"]
            time = timezone_timestamp(float(data["creationTime"]["usecSinceEpochUtc"])/1000000, self.app_config.TIMEZONE)
        else:
            merchant_name = None
            time = None


        for item in data["lineItem"]:
            landing_page = []
            address = None
            price = None
            name = None
            if item.get("purchase"):
                if item["purchase"].get("productInfo"):
                    _type="purchase"
                    name = item["purchase"]["productInfo"]["name"]
                    try:
                        price = item["purchase"]["unitPrice"]["displayString"]
                    except:
                        price = None

                    if item["purchase"].get("fulfillment"):
                        address = item["purchase"]["fulfillment"]["location"]["address"][0].replace("\n", ",")
                        landing_page = item["purchase"]["landingPageUrl"]["link"]
                    
                    products.append({"name": name, "address": address, "price": price, "landing_page": landing_page})
                
                else:
                    #DATA {'merchantOrderId': '21823872872', 'creationTime': {'usecSinceEpochUtc': '1538748693000000',
                    # 'granularity': 'MICROSECOND'}, 'transactionMerchant': {'name': 'swiggy.in'},
                    # 'lineItem': [{'purchase': {'status': 'DELIVERED'}}]} with error 'productInfo'

                    raise Exception("Unidentified type One, probably incomplete data")

            else:
                if item.get("flightReservation"):
                    _type="flights"
                    merchant_name = item["provider"]["name"]
                    time = timezone_timestamp(float(item["flightReservation"]["flightLeg"]["flightStatus"]["departureTime"]["usecSinceEpochUtc"])/1000000, self.app_config.TIMEZONE)
                    src = item["flightReservation"]["flightLeg"]["departureAirport"]["servesCity"]["name"]
                    dest = item["flightReservation"]["flightLeg"]["arrivalAirport"]["servesCity"]["name"]
                else:
                    raise Exception("Unidentified Type 2")

        return {"merchant_name": merchant_name,
                "time": time,
                "products": products,
                "dest": dest,
                "src": src,
                "type": _type,
                    }

    def parse_food_delivery(self):
        pass

    def parse_flight_reservation(self):
        pass

    def parse_train_reservation(self):
        pass

    def parse_cab_reservation(self):
        pass


