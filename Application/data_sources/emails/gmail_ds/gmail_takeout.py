
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

def indian_time_stamp(naive_timestamp=None):
    tz_kolkata = pytz.timezone('Asia/Kolkata')
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp.strftime(time_format + " %Z%z")


def month_aware_time_stamp(naive_timestamp=None): 
     tz_kolkata = pytz.timezone('Asia/Kolkata') 
     time_format = "%Y-%m-%d %H:%M:%S" 
     if naive_timestamp: 
         aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp)) 
     else: 
         naive_timestamp = datetime.datetime.now() 
         aware_timestamp = tz_kolkata.localize(naive_timestamp) 
     return {"timestamp": aware_timestamp.strftime(time_format + " %Z%z"), "year": aware_timestamp.year, "month": aware_timestamp.month} 


@asyncinit
class LocationHistory(object):
    
    async def __init__(self, gmail_takeout_path, db_dir_path):
        self.geolocator = Nominatim(user_agent="Datapod")
        self.db_dir_path = db_dir_path
        self.path = os.path.join(gmail_takeout_path, "Location History/Location History.json")
        self.pr_executor = concurrent.futures.ProcessPoolExecutor(max_workers=10)
        self.th_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.main_key = "location"
        self.location_db_data = {}
        if not os.path.exists(self.path):
            raise Exception("Reservations and purchase data doesnt exists")

    def most_visited(self):
        """
        res will be an updated list of dicts with each dict having a 
        month and year to it
        this will be only for a month of the year to calculate most visited 
        place of a month
        """
        hashed_dict  = {}
        for e in res: 
            um = str(e["latitudeE7"]) + str(e["longitudeE7"]) 
            _hash = hashlib.sha224(um.encode()).hexdigest() 
            if hashed_dict.get(_hash): 
                f = hashed_dict.get(_hash) 
                f.append(e) 
                hashed_dict[_hash] = f 
            else: 
                hashed_dict[_hash] = [f] 



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


    def store(self):
        self.db_instance = create_db_instance(self.db_dir_path)
        with open(self.path, "rb") as fi:
            result  = fi.read() 
            location = json.loads(result)

        location_data = location["locations"]
        #tasks = [self.reverse_geo_code(loc["latitudeE7"]/10000000, loc["longitudeE7"]/10000000) \
        #for loc in location_data]
    
        ##update the location history array with month and year
        for loc_data in location_data: 
            _t = month_aware_time_stamp(float(loc_data["timestampMs"])/1000)  
            loc_data.update(_t)
            self.push_db(loc_data, int(_t["month"]), int(_t["year"]))


        insert_key(self.main_key, self.location_db_data, self.db_instance)
        close_db_instance(self.db_instance)
        return 

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



class PurchaseReservations(object):
    
    def __init__(self, gmail_takeout_path, db_dir_path):
        self.db_dir_path = db_dir_path
        self.path = os.path.join(gmail_takeout_path, "Purchases _ Reservations")
        self.db_instance = create_db_instance(db_dir_path)
        if not os.path.exists(self.path):
            raise Exception("Reservations and purchase data doesnt exists")


    def parse(self):
        purchase = []
        reservations = []
        for filename in os.listdir(self.path):
            filepath = os.path.join(self.path, filename)
            with open(filepath, "r") as f: 
                data = json.loads(f.read()) 
                try: 
                    result = self.parse_purchase(data)
                    if result.get("type") == "purchase":
                        purchase.append(result)
                    else:
                        reservations.append(result)

                except Exception as e: 
                    logger.error(f"In DATA {data} error is  <<{e}>>")
            
        insert_key("gmail_purchase", purchase, self.db_instance)
        insert_key("gmail_reservations", reservations, self.db_instance)

        close_db_instance(self.db_instance)

    def parse_purchase(self, data): 
        address = None
        src = None
        dest = None
        address = None
        _type = None
        merchant_name = None
        if data.get("transactionMerchant"):
            merchant_name = data["transactionMerchant"]["name"] 
            time = indian_time_stamp(float(data["creationTime"]["usecSinceEpochUtc"])/1000000) 
        else:
            merchant_name = None 
            time = None
        
        items = [] 

        for item in data["lineItem"]: 
            if item.get("purchase"):
                if item["purchase"].get("productInfo"):
                    _type="purchase"
                    if item["purchase"].get("fulfillment"):
                        address = item["purchase"]["fulfillment"]["location"]["address"]

                    items.append(item["purchase"]["productInfo"]["name"])
                else:
                    #DATA {'merchantOrderId': '21823872872', 'creationTime': {'usecSinceEpochUtc': '1538748693000000', 
                    # 'granularity': 'MICROSECOND'}, 'transactionMerchant': {'name': 'swiggy.in'}, 
                    # 'lineItem': [{'purchase': {'status': 'DELIVERED'}}]} with error 'productInfo'

                    raise Exception("Unidentified type One, probably incomplete data")
            else:
                if item.get("flightReservation"):
                    _type="flights"
                    merchant_name = item["provider"]["name"]
                    time = indian_time_stamp(float(item["flightReservation"]["flightLeg"]["flightStatus"]["departureTime"]["usecSinceEpochUtc"])/1000000) 
                    src = item["flightReservation"]["flightLeg"]["departureAirport"]["servesCity"]["name"]
                    dest = item["flightReservation"]["flightLeg"]["arrivalAirport"]["servesCity"]["name"]
                else:
                    raise Exception("Unidentified Type 2")
        
        return {"merchant_name": merchant_name,  
                "time": time,  
                "products": items,
                "address": address,
                "dest": dest, 
                "src": src,
                "type": _type
                    } 
 

    def parse_food_delivery(self):
        pass

    def parse_flight_reservation(self):
        pass

    def parse_train_reservation(self):
        pass

    def parse_cab_reservation(self):
        pass






class GmailsEMTakeout(object):
    message_types = ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]
    def __init__(self, gmail_takeout_path, parsed_data_path):
        # self.db_dir_path = db_dir_path
        self.email_mbox = mailbox.mbox(gmail_takeout_path) 
        #self.email_dir_txt = os.path.join(parsed_data_path, "mails/gmail/emails_txt")
        
        # if not os.path.exists(self.email_dir_txt):
        #     logger.warning(f"Path doesnt exists creating {self.email_dir_txt}")
        #     os.makedirs(self.email_dir_txt) 

        
        self.email_dir_html = os.path.join(parsed_data_path, "mails/gmail/email_html")
        
        for message_type in  ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]:
            if not os.path.exists(self.email_dir_html):
                logger.warning(f"Path doesnt exists creating {self.email_dir_html}")
                os.makedirs(self.email_dir_html)

            self.image_dir = os.path.join(parsed_data_path, f"mails/gmail/images")
            if not os.path.exists(self.image_dir):
                logger.warning(f"Path doesnt exists creating {self.image_dir}")
                os.makedirs(self.image_dir) 



            self.image_dir_temp = os.path.join(self.image_dir, "temp")
            if not os.path.exists(self.image_dir_temp):
                logger.warning(f"Path doesnt exists creating {self.image_dir_temp}")
                os.makedirs(self.image_dir_temp)

            ##creating sub sirectories for image formats 

            self.image_dir_png = os.path.join(self.image_dir, "png")
            if not os.path.exists(self.image_dir_png):
                logger.warning(f"Path doesnt exists creating {self.image_dir_png}")
                os.makedirs(self.image_dir_png)


            self.image_dir_small = os.path.join(self.image_dir, "small")
            if not os.path.exists(self.image_dir_small):
                logger.warning(f"Path doesnt exists creating {self.image_dir_small}")
                os.makedirs(self.image_dir_small)



            self.image_dir_junk = os.path.join(self.image_dir, "junk")
            if not os.path.exists(self.image_dir_junk):
                logger.warning(f"Path doesnt exists creating {self.image_dir_junk}")
                os.makedirs(self.image_dir_junk)



            self.image_dir_normal = os.path.join(self.image_dir, "normal")
            if not os.path.exists(self.image_dir_normal):
                logger.warning(f"Path doesnt exists creating {self.image_dir_normal}")
                os.makedirs(self.image_dir_normal)



            self.pdf_dir = os.path.join(parsed_data_path, "mails/gmail/pdfs")
            if not os.path.exists(self.pdf_dir):
                logger.warning(f"Path doesnt exists creating {self.pdf_dir}")
                os.makedirs(self.pdf_dir) 


            self.extra_dir = os.path.join(parsed_data_path, "mails/gmail/extra")
            if not os.path.exists(self.extra_dir):
                logger.warning(f"Path doesnt exists creating {self.extra_dir}")
                os.makedirs(self.extra_dir) 
        logger.info("App intiation been done")





    def download_emails(self):
        """
        Downloding list of emails from the gmail server
        for message in self.email_mbox: 
            print (message["subject"], message["to"], message["from"]) message["X-Gmail-Labels"]
          if from_data.get(message["from"]): 
              from_data[message["from"]]+=1 
          else: 
              from_data[message["from"]] = 1 
              dsdsdsas 

        """
        #db_instance = create_db_instance(self.db_dir_path)
        db_instance = None

        i = 0
        for message in self.email_mbox: 
            #email_uid = self.emails[0].split()[x]
            email_from, email_to, subject, local_message_date, email_message = message["From"], \
                    message["To"], message["Subject"], message["Date"], message
            self.save_email(email_from, email_to, subject, local_message_date, email_message, db_instance)
            i += 1
            if i%100 == 5:
                break
                logger.info(f"NUmber of emails saved {i}")
        logger.info(f"\n\nTotal number of emails {i}\n\n")




        # ########### logs update for gmail #######
        # stored_value = get_key("logs", db_instance)

        # value = [{"date": indian_time_stamp(), 
        #         "status": "success", 
        #         "message": "Gmail takeout has been parsed successfully"}]
        
        # if stored_value:
        #     value = value+stored_value  
    
        # logger.info(f"value stored against logs is {value}")
        # insert_key("logs", value, db_instance)

        # ########### services update for gmail #######
        # value = [{"time": indian_time_stamp(), 
        #     "service": "gmail", 
        #     "message": f"{i} emails present"}]
    
        # stored_value = get_key("services", db_instance)
        # logger.info("Stored value against services %s"%stored_value)
        
        # if stored_value:
            
        #     for entry in stored_value:
        #         if entry.get("service") == "gmail":
        #             break
        #     stored_value.remove(entry)
        #     stored_value.extend(value)
        # else:
        #     stored_value = value

        # insert_key("services", stored_value, db_instance)
        # close_db_instance(db_instance)
        return 



    def extract_email_from(self, message_from):
        try:
            match = re.findall(r'@[\S\.]+\.', message_from) 
            result = match[0].replace("@", "").split(".")

            sender_dir_name = result[-2: -1][0] 

            try:
                sender_sub_dir_name = result[:-2][0]
                return sender_dir_name, sender_sub_dir_name
            except:
                return sender_dir_name, "main"

            logger.info(f"for message_from<{message_from}> the sender_dir_name {sender_dir_name} and sender_sub_dir_name {sender_sub_dir_name}")
            return sender_dir_name, sender_sub_dir_name                

        except Exception as err: 
            logger.error(err.__str__())
            logger.error(f"Something went wrong in classifying {message_from}")
            return "unknown", "unknown"

        return

    def convert_to_epoch(self, date):
        """
        "Tue, 7 Nov 2017 07:53:50 +0000"


        """
        if not date: 
              return 0 
        else: 
            try: 
                result = re.sub("[\(\[].*?[\)\]]", "", date) 
                result = parser.parse(result.strip()).timestamp() 
            except Exception as err: 
                logger.error(f"Error parsing {date} with error {err}") 
                return 0
        return int(result)

    def remove_html(self, html_body):
        if isinstance(html_body, bytes):
            html_body = self.handle_encoding(html_body)
        k = bleach.clean(html_body, tags=[], attributes={}, styles=[], strip=True).replace("\n", "")                                                                                                                                                                                       

        return ' '.join(k.split())


    def handle_encoding(self, data):
        try:
            return data.decode() ##defaultis utf-8
        except Exception as err:
            try:
                #logger.error(f"Error decoding html_body {data} with error {err}")
                return data.decode('unicode_escape')
            except Exception as err:
                logger.error(f"While encoding unicode_Escape {err}")
                return "The bytes couldnt be decoded"

    def format_filename(self, filename):
        return re.sub('[^\w\-_\. ]', '_', filename).replace(" ", "")


    def save_email(self, email_from, email_to, subject, local_message_date, email_message, db_instance):
        # Body details
        #logger.info(f"email_from={email_from}, email_to={email_to}, subject={subject}, local_message_date={local_message_date}")
        print (dir(email_message))
        message_type = message.get("X-Gmail-Labels").split(",")[0]


        if message_type not in ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]:
            message_type = "Inbox"


        sender_dir_name, sender_sub_dir_name = self.extract_email_from(email_from)
        self.ensure_directory(sender_dir_name, sender_sub_dir_name)

        epoch = self.convert_to_epoch(local_message_date)

        file_name_html = "email_" + str(epoch) + ".html"
        #multipart/mixed,  multipart/alternative, multipart/related, text/html
        body = ""
        html_body = ""
        attachments = "\n"
        sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)

        
        
        sender_sub_dir_html = os.path.join(f"{self.email_dir_html}/{sender_dir_name}", sender_sub_dir_name)
        file_path_html = os.path.join(sender_sub_dir_html, file_name_html)
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    nbody = part.get_payload(decode=True)  # decode
                    body = body + self.handle_encoding(nbody)

                elif ctype == 'text/html' and 'attachment' not in cdispo:
                    ##this is generally the same as text/plain but has 
                    ##html embedded into it. save it another file with 
                    ##html extension
                    hbody = part.get_payload(decode=True)  # decode
                    html_body = html_body + self.handle_encoding(hbody)

                elif ctype in  ["multipart/alternative", "multipart/related", "multipart/mixed"] and "attachment" not in cdispo:
                    ##this is generally the same as text/plain but has 
                    ##html embedded into it. save it another file with 
                    ##html extension
                    mbody = part.get_payload(decode=True)  # decode
                    if mbody:

                        logger.error(f"Body found in multipary ctype {mbody}")


                else:
                    ##most of the times, this code block will have junk mime 
                    ##type except the attachment part 

                    if part.get_filename():

                        #attachment_name = part.get_filename() + "__"+ str(email_uid)
                        ##prefix attachment with TAGS like BANK, CAB, 
                        _attachment_name = f"{sender_dir_name}_{sender_sub_dir_name}_{epoch}_{part.get_filename()}"
                        attachment_name = self.format_filename(_attachment_name)


                        if ctype.startswith("image"):
                            _image_path = os.path.join(self.image_dir_temp, attachment_name)
                            with open(_image_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            image_data = {"path": _image_path, "email_html": file_path_html}
                            #ins = StoreInChunks("gmail",  image_data, db_instance)
                            #image_path = ins.image_path
                            #ins.insert()
                            # with open(image_path, "wb") as f:
                            #     f.write(part.get_payload(decode=True))
                                
                        
                        elif ctype == "application/pdf" or ctype =="application/octet-stream":
                            
                            pdf_path = os.path.join(self.pdf_dir, attachment_name)
                            with open(pdf_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                                data = {"path": pdf_path, "email_html": file_path_html}
                                # ins = StoreInChunks("gmail",  data, db_instance, "gmail_pdf")
                                # ins.insert()
                        


                        else:
                            logger.error(f" MIME type {ctype} with a file_name {attachment_name}")
                            extra_path = os.path.join(self.extra_dir, attachment_name)
                            with open(extra_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                                # data = {"path": extra_path, "email_html": file_path_html, "email_text": file_path_text}
                                # ins = StoreInChunks("gmail",  data, db_instance, "gmail_extra")
                                # ins.insert()
                        #logger.info(f"Attachment with name {attachment_name} and content_type {ctype} found")            

                        attachments += f"{attachment_name}\n"
                        logger.info(f"Ctype is {ctype} and attachment name is {attachment_name}")
                        
                    else:
                        logger.error(f"Mostly junk MIME type {ctype} without a file_name")


            if DEBUG:
                # not multipart - i.e. plain text, no attachments, keeping fingers crossed
                pprint(body)

        else:
            #when the email is just plain text
            body = email_message.get_payload(decode=True)
            #logger.error(f"email with Plaintext found, Which is rare {email_message.is_multipart()} email from {email_from}")

        nl = "\r\n"


            
        # # text = self.remove_html(body)
        # if isinstance(body, str):
        #     html_body = html_body.encode()

        if not html_body:
            try:
                if isinstance(body, str):
                    html_body = body.replace("\r", "").replace("\n", "")
                else:
                    html_body = body.decode().replace("\r", "").replace("\n", "")
            except Exception as e:
                print (e)
                print (body)
                return 
                                                                                                                                                                                                                                                           

        with open(file_path_html, "wb") as f:
            data = f"From: {email_from}{nl}To: {email_to}{nl}Date: {local_message_date}{nl}Attachments:{attachments}{nl}Subject: {subject}{nl}\nBody: {nl}{html_body}"
            if DEBUG:
                logger.info(f"HTML BODY {data}")
            f.write(data.encode())

        return 



    def ensure_directory(self, sender_dir_name, sender_sub_dir_name):
        
        sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)
        if not os.path.exists(sender_sub_dir_txt):
            logger.info(f"Creating directory TXT messages{sender_sub_dir_txt}")
            os.makedirs(sender_sub_dir_txt) 
        

        sender_sub_dir_html = os.path.join(f"{self.email_dir_html}/{sender_dir_name}", sender_sub_dir_name)
        if not os.path.exists(sender_sub_dir_html):
            logger.info(f"Creating directory HTML messages {sender_sub_dir_html}")
            os.makedirs(sender_sub_dir_html) 
        
        return sender_sub_dir_txt, sender_sub_dir_html


    def prefix_attachment_name(self, filename, email_uid, email_subject, email_from):

        if BankStatements.is_bank_statement(email_subject):
            prefix = BankStatements.which_bank(email_subject)

        elif CabService.is_cab_service(email_subject):
            prefix = CabService.which_cab_service(email_from, email_subject)

        else:
            prefix = "UNKNOWN"

        return f"{prefix}_{email_uid}_{filename}"



if __name__ == "__main__":
    user_data_path = "/home/feynman/.Datapod/data"
    path =f"{user_data_path}/Takeout/Mail/All mail Including Spam and Trash.mbox"  
    parsed_data_path = "/home/feynman/.Datapod/parsed"
    instance = GmailsEMTakeout(path, parsed_data_path)
    instance.download_emails()
