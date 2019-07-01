
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
import datetime
import bleach
import json

# from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, StoreInChunks
import time
from asyncinit import asyncinit
import pytz
import asyncio
import concurrent
from utils.utils import timezone_timestamp, month_aware_time_stamp
import coloredlogs, verboselogs, logging
from geopy.geocoders import Nominatim
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


class TakeoutEmails(object):
    message_types = ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]
    def __init__(self, config):
        # self.db_dir_path = db_dir_path
        self.email_dir = os.path.join(config.RAW_DATA_PATH,  "Takeout/Mail/All mail Including Spam and Trash.mbox")
        self.email_mbox = mailbox.mbox(self.email_dir)
        
        self.email_dir_html = os.path.join(config.PARSED_DATA_PATH, "mails/gmail/email_html")
        
        for message_type in  ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]:
            if not os.path.exists(self.email_dir_html):
                logger.warning(f"Path doesnt exists creating {self.email_dir_html}")
                os.makedirs(self.email_dir_html)

            self.image_dir = os.path.join(config.PARSED_DATA_PATH, f"mails/gmail/images")
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



            self.pdf_dir = os.path.join(config.PARSED_DATA_PATH, "mails/gmail/pdfs")
            if not os.path.exists(self.pdf_dir):
                logger.warning(f"Path doesnt exists creating {self.pdf_dir}")
                os.makedirs(self.pdf_dir) 


            self.extra_dir = os.path.join(config.PARSED_DATA_PATH, "mails/gmail/extra")
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
        #db_instance = None

        i = 0
        for message in self.email_mbox: 
            #email_uid = self.emails[0].split()[x]
            logger.info(message)
            logger.info(message["From"])
            
            email_from, email_to, subject, local_message_date, email_message = message["From"], \
                    message["To"], message["Subject"], message["Date"], message
            self.save_email(email_from, email_to, subject, local_message_date, email_message)
            logger.info("\n\n\n")                
            i += 1
            if i%10 == 1:
                break
                logger.info(f"NUmber of emails saved {i}")
        logger.info(f"\n\nTotal number of emails {i}\n\n")




        # ########### logs update for gmail #######
        # stored_value = get_key("logs", db_instance)

        # value = [{"date": timezone_timestamp(), 
        #         "status": "success", 
        #         "message": "Gmail takeout has been parsed successfully"}]
        
        # if stored_value:
        #     value = value+stored_value  
    
        # logger.info(f"value stored against logs is {value}")
        # insert_key("logs", value, db_instance)

        # ########### services update for gmail #######
        # value = [{"time": timezone_timestamp(), 
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


    def save_email(self, email_from, email_to, subject, local_message_date, email_message):
        # Body details
        #logger.info(f"email_from={email_from}, email_to={email_to}, subject={subject}, local_message_date={local_message_date}")
        print (dir(email_message))
        message_type = email_message.get("X-Gmail-Labels").split(",")[0]


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
        #sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)

        
        
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


            # if DEBUG:
            #     # not multipart - i.e. plain text, no attachments, keeping fingers crossed
            #     pprint(body)

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
            
            logger.info(f"HTML BODY {data}")
            f.write(data.encode())

        return 



    def ensure_directory(self, sender_dir_name, sender_sub_dir_name):
        
        # sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)
        # if not os.path.exists(sender_sub_dir_txt):
        #     logger.info(f"Creating directory TXT messages{sender_sub_dir_txt}")
        #     os.makedirs(sender_sub_dir_txt) 
        

        sender_sub_dir_html = os.path.join(f"{self.email_dir_html}/{sender_dir_name}", sender_sub_dir_name)
        if not os.path.exists(sender_sub_dir_html):
            logger.info(f"Creating directory HTML messages {sender_sub_dir_html}")
            os.makedirs(sender_sub_dir_html) 
        
        return sender_sub_dir_html


    def prefix_attachment_name(self, filename, email_uid, email_subject, email_from):

        if BankStatements.is_bank_statement(email_subject):
            prefix = BankStatements.which_bank(email_subject)

        elif CabService.is_cab_service(email_subject):
            prefix = CabService.which_cab_service(email_from, email_subject)

        else:
            prefix = "UNKNOWN"

        return f"{prefix}_{email_uid}_{filename}"




