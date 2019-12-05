
from loguru import logger
from lxml.html.clean import Cleaner
import sys
import requests
import time
import os
from dputils.utils import timezone_timestamp, month_aware_time_stamp
from errors_module.errors import APIBadRequest, DuplicateEntryError
import pytz
from asyncinit import asyncinit
import time
import hashlib
import lxml
import json
import bleach
from dateutil import parser
import re
import base64
import mailbox
import imaplib
import email
import datetime
import hashlib
import datetime
import concurrent.futures
import aiomisc
#from tenacity import *
# from database_calls.takeout.db_emails import store_email, store_email_attachment, store_email_content
from email.header import Header, decode_header, make_header


from ..db_calls import store_email, store_email_attachment, store_email_content, update_percentage
from ..variables import DATASOURCE_NAME
import os 
import chardet
import subprocess
# from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, StoreInChunks









def folder_size(path='.'): 
    total = 0 
    for entry in os.scandir(path): 
        if entry.is_file(): 
            total += entry.stat().st_size 
        elif entry.is_dir(): 
            total += folder_size(entry.path) 
    return total 











@asyncinit
class EmailParse(object):

    #message_types = ["Sent", "Inbox", "Archived", "Starred", "Drafts", "Chat"]

    async def __init__(self, config, dest_path, username, checksum):
    
        ##to keep track of all the to_addr email ids and their respective frequencies 
        # self.db_dir_path = db_dir_path
        ## dest_path : path for the destination like ex /home/feynman/.datapod/userdata/raw/Google/houzier.saurav@gmail.com/16-10-2019-56c3eccc615e71f1e2fcd0d0b07220532947651bc13c0e0fdfa621a2a1783c35/
        self.config = config
        self.dest_path = dest_path
        self.checksum = checksum
        self.username = username

        self.email_path = os.path.join(dest_path,  "Takeout/Mail")

        self.mbox_objects = []
        total_emails = []



        self.email_dir_size = folder_size(self.email_path)

        ##calculate approximate number of emails 
        self.approximate_email_count = int(self.email_dir_size//(1024*128*1.4))

        self.mbox_file_names = os.listdir(self.email_path)
        logger.info(self.mbox_file_names)

        ##listing all the .mbox files present in the Takeout/Mail directory
        # for mbox_file in os.listdir(self.email_path):
            

        #     path = os.path.join(self.email_path, mbox_file)

        #     #mbox_object = mailbox.mbox(path)
        #     mbox_object = await self.read_mbox(path)
        #     email_count = len(mbox_object.keys())

        #     if mbox_file == "All mail Including Spam and Trash.mbox":
        #         self.mbox_objects.append({
        #                 "mbox_type": "Inbox", 
        #                 "mbox_object": mbox_object,
        #                 "email_count": email_count
        #         })

        #     else:
        #         self.mbox_objects.append({
        #                 "mbox_type": mbox_file.replace(".mbox", ""), 
        #                 "mbox_object": mbox_object,
        #                 "email_count": email_count
        #         })

        #     total_emails.append(email_count)

        # step = sum(total_emails)//97


        # start = 0
        # for mbox_object in self.mbox_objects:
        #     try:
        #         end = mbox_object["email_count"]//step 
        #     except:
        #         end = 15
        #         step = 1
        #     mbox_object.update({"start": start*step, "end": (start+end)*step, "step": step}) 
        #     start = start+end 


        # start = 0
        # for mbox_object in self.mbox_objects:
        #     try:
        #         end = mbox_object["email_count"]//step 
        #     except:
        #         end = 15
        #         step = 1
        #     mbox_object.update({"start": start*step, "end": (start+end)*step, "step": step}) 
        #     start = start+end 




        # logger.info(f"Total number of emails {sum(total_emails)}")        
        # logger.info(f"Mbox objects {self.mbox_objects}")        
        # self.email_count = sum(total_emails)
    

    @aiomisc.threaded_separate
    def read_mbox(self, path):
        logger.info(f"Reading {path}")
        mbox_object = mailbox.mbox(path)
        logger.success(f"Read {path}")
        return mbox_object


    async def download_emails(self):

        ##if emails are less than 100, then step will be 0

        logger.info(f"Aproximate number of emails are {self.approximate_email_count}")
        step = self.approximate_email_count//95
        logger.info(f"Step is  {step}")
        
        

        res = {"message": "PROGRESS", "percentage": 1}

        await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
        await update_percentage(self.config[DATASOURCE_NAME]["tables"]["status_table"], DATASOURCE_NAME, self.username, 1)


        start = 0

        logger.info("What the fuck one")
        for mbox_file_name in self.mbox_file_names:
            logger.info("What the fuck Two")
            mbox_type = mbox_file_name.replace(".mbox", "")

            if mbox_file_name == "All mail Including Spam and Trash.mbox":
                mbox_type = "Inbox"

            mbox_path = os.path.join(self.email_path, mbox_file_name)
            mbox_object = await self.read_mbox(mbox_path)
            email_count = len(mbox_object.keys())
            # try:
            #     end = email_count//step 
            # except:
            #     end = 100
            #     step = 1
            
            end = start+email_count

            
            logger.warning(f"Start is {start} END is {end} Step is {step} Email count is {email_count}, MBOX type is {mbox_type}")

            instance = Emails(self.config,  self.dest_path, self.username, self.checksum, mbox_object, mbox_type, 
                                email_count, step, 
                                start, end)
            start = end
            await instance.download_emails()
            if mbox_type == "Inbox":
                self.email_id = max(instance._to_addr_dict, key=instance._to_addr_dict.get)

            del mbox_object
        





class Emails(object):
    message_types = ["Sent", "Inbox", "Archived", "Starred", "Drafts", "Chat"]
    
    def __init__(self, config, dest_path, username, checksum, mbox_object, mbox_type, email_count, step, start, end):

        self.config = config
        self.username = username
        self.checksum = checksum
        self.step = step
        self.start = start
        self.end = end
        ##to keep track of all the to_addr email ids and their respective frequencies 
        self._to_addr_dict = {}
        # self.db_dir_path = db_dir_path
        self.email_dir = os.path.join(dest_path,  "Takeout/Mail/Inbox.mbox")
        # self.archived_dir = os.path.join(config.RAW_DATA_PATH,  "Takeout/Mail/Archived.mbox")
        # self.sent_dir = os.path.join(config.RAW_DATA_PATH,  "Takeout/Mail/Sent.mbox")
        # self.starred_dir = os.path.join(config.RAW_DATA_PATH,  "Takeout/Mail/Starred.mbox")
        # self.drafts_dir = os.path.join(config.RAW_DATA_PATH,  "Takeout/Mail/Drafts.mbox")
        # self.chat_dir = os.path.join(config.RAW_DATA_PATH,  "Takeout/Mail/Chat.mbox")


        self.email_mbox = mbox_object
        self.mbox_type = mbox_type
        self.email_count = email_count
        self.email_dir_html = os.path.join(config.PARSED_DATA_PATH, DATASOURCE_NAME, self.username, "mails/gmail/email_html")

        self.email_table = config[DATASOURCE_NAME]["tables"]["email_table"]
        # this wil store the content of the email to be s
        # this is a seperate table which will store the attachments of the
        # the emailearchable through content
        # store subject+content+to_addr in this as a content
        self.indexed_email_content_tbl = config[DATASOURCE_NAME]["tables"]["email_content_table"]

        self.email_attachements_tbl = config[DATASOURCE_NAME]["tables"]["email_attachment_table"]
        self.status_table = config[DATASOURCE_NAME]["tables"]["status_table"]

        if not os.path.exists(self.email_dir_html):
            logger.warning(f"Path doesnt exists creating {self.email_dir_html}")
            os.makedirs(self.email_dir_html)

        ##Creating iimage directory for the emails
        self.image_dir = os.path.join(config.PARSED_DATA_PATH, f"mails/gmail/images")
        if not os.path.exists(self.image_dir):
            logger.warning(f"Path doesnt exists creating {self.image_dir}")
            os.makedirs(self.image_dir)

        self.image_dir_temp = os.path.join(self.image_dir, "temp")
        if not os.path.exists(self.image_dir_temp):
            logger.warning(f"Path doesnt exists creating {self.image_dir_temp}")
            os.makedirs(self.image_dir_temp)

        # creating sub sirectories for image formats
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

        ##Since the takeout has started we need to update the datasources table in DB eith
        ## the flag Progress


    #async def download_emails(self, loop, executor):
    @logger.catch
    async def download_emails(self):
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

        self._email_count = 0

        completion_percentage = list(range(self.start, self.end, self.step)) 
        logger.info(f"Completion percentage is {completion_percentage}")
        i = 0
        for message in self.email_mbox:
            #email_uid = self.emails[0].split()[x]
            self.start += 1
            i += 1
            
            try:
                await self.save_email(message)
            except Exception as e:
                logger.error(e)
                pass
            
            if completion_percentage:
                logger.info(f"Email number is {i}")
                if self.start in completion_percentage:
                    #logger.info(f"I found {i}")
                    # percentage = f"{completion_percentage.index(i) +1 }"
                    percentage = (self.start+self.step)//self.step
                    logger.info(f"Percentage of completion {percentage}% at {self.start} emails")

                    res = {"message": "PROGRESS", "percentage": int(percentage)}

                    await self.config["send_sse_message"](self.config, DATASOURCE_NAME, res)
                    await update_percentage(self.status_table, DATASOURCE_NAME, self.username, int(percentage))
    
            

            if i == 500:
                break

        logger.info(f"\n\nTotal number of emails {self.email_count}\n\n")
        
       
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

            logger.info(
                f"for message_from<{message_from}> the sender_dir_name {sender_dir_name} and sender_sub_dir_name {sender_sub_dir_name}")
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



    def _is_etree(self, tree):
        if not isinstance(tree, lxml.etree.ElementBase):
            raise Exception("you're passing something that's not an etree")

    def get_clean_html(self, html_text, text_only=True):
        try:
            etree = lxml.html.document_fromstring(html_text)

            self._is_etree(etree)
            # enable filters to remove Javascript and CSS from HTML document
            cleaner = Cleaner()
            cleaner.javascript = True
            cleaner.style = True
            cleaner.html = True
            cleaner.page_structure = False
            cleaner.meta = False
            cleaner.safe_attrs_only = False
            cleaner.links = False

            html = cleaner.clean_html(etree)
            if text_only:
                return ' '.join(html.text_content().split())
                # return html.text_content()

            res = lxml.html.tostring(html)
        except Exception as e:
            logger.error(f"While parsing email in get_clean_html {e}")
            res = "junk"

        return res 

    def handle_encoding(self, data):
        try:
            return data.decode()  # defaultis utf-8
        except Exception as err:
            try:
                #logger.error(f"Error decoding html_body {data} with error {err}")
                return data.decode('unicode_escape')
            except Exception as err:
                logger.error(f"While encoding unicode_Escape {err}")
                return "The bytes couldnt be decoded"

    def __format_filename(self, filename):
        return re.sub('[^\w\-_\. ]', '_', filename).replace(" ", "")

    def __message_id(self, email_message):
        try:
            raw_id = email_message["Message-ID"].encode()
            message_id = hashlib.sha3_256(raw_id).hexdigest()
        except:
            message_id = os.urandom(32).hex()
            raw_id = "junk"
        return raw_id, message_id

    def __add_to_addr_address(self, email_address):
        if self._to_addr_dict.get(email_address):
            self._to_addr_dict[email_address] += 1
        else:
            self._to_addr_dict[email_address] = 1
        return 
    
    async def save_email(self, email_message):
        email_from = email_message["From"]
        email_to = email_message["To"]
        subject = email_message["Subject"]
        local_message_date = email_message["Date"]

        self.__add_to_addr_address(email_to)

        #message_type = email_message.get("X-Gmail-Labels")

        
        sender_dir_name, sender_sub_dir_name = self.extract_email_from(
            email_from)
        self.ensure_directory(sender_dir_name, sender_sub_dir_name)

        epoch = self.convert_to_epoch(local_message_date)

        file_name_html = "email_" + str(epoch) + ".html"
        #multipart/mixed,  multipart/alternative, multipart/related, text/html
        body = ""
        html_body = ""
        attachments = []
        #sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)

        sender_sub_dir_html = os.path.join(
            f"{self.email_dir_html}/{sender_dir_name}", sender_sub_dir_name)
        file_path_html = os.path.join(sender_sub_dir_html, file_name_html)
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()

                charset = part.get_content_charset()

                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    # nbody = part.get_payload(decode=True)  # decode
                    # body = body + self.handle_encoding(nbody)
                    text = str(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace').decode()
                    body = body + text
                

                elif ctype == 'text/html' and 'attachment' not in cdispo:
                    # this is generally the same as text/plain but has
                    # html embedded into it. save it another file with
                    # html extension
                    # hbody = part.get_payload(decode=True)  # decode
                    # html_body = html_body + self.handle_encoding(hbody)

                    hbody = str(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace').decode()
                    html_body = html_body + hbody


                elif ctype in ["multipart/alternative", "multipart/related", "multipart/mixed"] and "attachment" not in cdispo:
                    # this is generally the same as text/plain but has
                    # html embedded into it. save it another file with
                    # html extension
                    mbody = part.get_payload(decode=True)  # decode
                    if mbody:

                        logger.error(f"Body found in multipary ctype {mbody}")

                else:
                    # most of the times, this code block will have junk mime
                    # type except the attachment part

                    if part.get_filename():


                        attachment_name = part.get_filename()
                        attachment_name=self.__format_filename(attachment_name)

                        if ctype.startswith("image"):

                            image_path = os.path.join(
                                self.image_dir_temp, attachment_name)
                            with open(image_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments.append(image_path)
                            
                        elif ctype == "application/pdf" or ctype == "application/octet-stream":
                            pdf_path = os.path.join(
                                self.pdf_dir, attachment_name)
                            with open(pdf_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments.append(pdf_path)
                            

                        else:
                            # logger.error(
                            #     f" MIME type {ctype} with a file_name {attachment_name}")
                            extra_path = os.path.join(
                                self.extra_dir, attachment_name)
                            with open(extra_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments.append(extra_path)
                            
             
                        # logger.info(
                        #     f"Ctype is {ctype} and attachment name is {attachment_name}")

                    else:
                        # logger.error(
                        #     f"Mostly junk MIME type {ctype} without a file_name")
                        pass

        else:
            # when the email is just plain text
            #body = email_message.get_payload(decode=True)
            #logger.error(f"email with Plaintext found, Which is rare {email_message.is_multipart()} email from {email_from}")
            text = str(email_message.get_payload(decode=True), email_message.get_content_charset(), 'ignore').encode('utf8', 'replace').decode()
            body = text.strip()

        nl = "\r\n"

        # # text = self.remove_html(body)
        # if isinstance(body, str):
        #     html_body = html_body.encode()

        # if not html_body:
        #     try:
        #         if isinstance(body, str):
        #             html_body = body.replace("\r", "").replace("\n", "")
        #         else:
        #             html_body = body.decode().replace("\r", "").replace("\n", "")
        #     except Exception as e:
        #         logger.error(e)
        #         logger.error(body)
        #         return

        email_text = body
        if not email_text:
            email_text = self.get_clean_html(html_body)

        
        with open(file_path_html, "wb") as f:
            #data = f"From: {email_from}{nl}To: {email_to}{nl} Date: {local_message_date}{nl}Attachments:{attachments}{nl}Subject: {subject}{nl}\nBody: {nl}{html_body}"
            f.write(html_body.encode())

        raw_id, message_id = self.__message_id(email_message)

        data = {"email_id": message_id, 
                "email_id_raw": raw_id,
                "from_addr" : email_from,
                "subject": subject,
                "to_addr": email_to,
                "content": email_text,
                "date": datetime.datetime.utcfromtimestamp(epoch),
                "path": file_path_html,
                "username": self.username,
                "checksum": self.checksum,
                "attachments": False,
                "message_type": self.mbox_type}
        

        if attachments:
            data.update({"attachments": True})

        await self.store(attachments, data)

        # if attachments:
        #     logger.info(f"This is the attachement array {attachments}")
        self.email_count +=1 
        return 


    async def store(self, attachments, data):
        if attachments:
            data.update({"attachments": True})
            
        try:
    
            data.update({"tbl_object": self.email_table})
            await store_email(**data)

            ##storing email content in different table, make searchable
            ##if only insertion of email is successful, insertion of indexed content 
            ##will happem , indexing on FTS5 table is not allowed so we have to adopt this 
            ##stategy nby making assumption that if a key for email exists so is the indexed content
            data.update({"tbl_object": self.indexed_email_content_tbl})
            try:
                content = data["content"] + data["subject"] + data["to_addr"]
            except Exception as e:
                logger.error(decode_header(data["subject"]))
                content = data["content"]

            content_hash = hashlib.sha256(content.encode()).hexdigest()
            data.update({"content": content, "content_hash": content_hash})
        
            await store_email_content(**data)
        except DuplicateEntryError as e:
            # logger.error(e)
            # logger.info("Skipping indexed email content entry")
            pass
        except Exception as e:
            logger.info(e)
            pass

        data.update({"tbl_object": self.email_attachements_tbl})
        for attachment_path in attachments:
            data.update({"path": attachment_path, "attachment_name" :attachment_path.split("/")[-1], "message_type": data["message_type"]})
            await store_email_attachment(**data)

        
        return 


    def ensure_directory(self, sender_dir_name, sender_sub_dir_name):
        # sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)
        # if not os.path.exists(sender_sub_dir_txt):
        #     logger.info(f"Creating directory TXT messages{sender_sub_dir_txt}")
        #     os.makedirs(sender_sub_dir_txt)

        sender_sub_dir_html = os.path.join(
            f"{self.email_dir_html}/{sender_dir_name}", sender_sub_dir_name)
        if not os.path.exists(sender_sub_dir_html):
            logger.info(
                f"Creating directory HTML messages {sender_sub_dir_html}")
            os.makedirs(sender_sub_dir_html)

        return sender_sub_dir_html

