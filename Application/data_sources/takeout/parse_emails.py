
import logging
import verboselogs
import coloredlogs
from lxml.html.clean import Cleaner
import sys
import os
from utils.utils import timezone_timestamp, month_aware_time_stamp
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
import asyncio
import functools
from tenacity import *
from database_calls.db_emails import store_email, store_email_attachment, store_email_content
from database_calls.db_profile import store_datasource

SERVER = "imap.gmail.com"
# from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key, StoreInChunks

verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


class TakeoutEmails(object):
    message_types = ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]
    __source__ = "google"
    
    def __init__(self, config):

        ##to keep track of all the to_addr email ids and their respective frequencies 
        self._to_addr_dict = {}
        # self.db_dir_path = db_dir_path
        self.email_dir = os.path.join(
            config.RAW_DATA_PATH,  "Takeout/Mail/All mail Including Spam and Trash.mbox")
        self.email_mbox = mailbox.mbox(self.email_dir)

        self.email_dir_html = os.path.join(
            config.PARSED_DATA_PATH, "mails/gmail/email_html")

        self.email_table = config.EMAILS_TBL

        # this wil store the content of the email to be searchable through content
        # store subject+content+to_addr in this as a content
        self.indexed_email_content_tbl = config.INDEX_EMAIL_CONTENT_TBL

        self.datasources_tbl = config.DATASOURCES_TBL
        # this is a seperate table which will store the attachments of the
        # the email
        self.email_attachements_tbl = config.EMAIL_ATTACHMENT_TBL

        for message_type in ["Sent", "Inbox", "Spam", "Trash", "Drafts", "Chat"]:
            if not os.path.exists(self.email_dir_html):
                logger.warning(
                    f"Path doesnt exists creating {self.email_dir_html}")
                os.makedirs(self.email_dir_html)

            self.image_dir = os.path.join(
                config.PARSED_DATA_PATH, f"mails/gmail/images")
            if not os.path.exists(self.image_dir):
                logger.warning(f"Path doesnt exists creating {self.image_dir}")
                os.makedirs(self.image_dir)

            self.image_dir_temp = os.path.join(self.image_dir, "temp")
            if not os.path.exists(self.image_dir_temp):
                logger.warning(
                    f"Path doesnt exists creating {self.image_dir_temp}")
                os.makedirs(self.image_dir_temp)

            # creating sub sirectories for image formats

            self.image_dir_png = os.path.join(self.image_dir, "png")
            if not os.path.exists(self.image_dir_png):
                logger.warning(
                    f"Path doesnt exists creating {self.image_dir_png}")
                os.makedirs(self.image_dir_png)

            self.image_dir_small = os.path.join(self.image_dir, "small")
            if not os.path.exists(self.image_dir_small):
                logger.warning(
                    f"Path doesnt exists creating {self.image_dir_small}")
                os.makedirs(self.image_dir_small)

            self.image_dir_junk = os.path.join(self.image_dir, "junk")
            if not os.path.exists(self.image_dir_junk):
                logger.warning(
                    f"Path doesnt exists creating {self.image_dir_junk}")
                os.makedirs(self.image_dir_junk)

            self.image_dir_normal = os.path.join(self.image_dir, "normal")
            if not os.path.exists(self.image_dir_normal):
                logger.warning(
                    f"Path doesnt exists creating {self.image_dir_normal}")
                os.makedirs(self.image_dir_normal)

            self.pdf_dir = os.path.join(
                config.PARSED_DATA_PATH, "mails/gmail/pdfs")
            if not os.path.exists(self.pdf_dir):
                logger.warning(f"Path doesnt exists creating {self.pdf_dir}")
                os.makedirs(self.pdf_dir)

            self.extra_dir = os.path.join(
                config.PARSED_DATA_PATH, "mails/gmail/extra")
            if not os.path.exists(self.extra_dir):
                logger.warning(f"Path doesnt exists creating {self.extra_dir}")
                os.makedirs(self.extra_dir)
        logger.info("App intiation been done")


    def __update_source_table(self, email_count):
        """
        Update data sources table after successful parsing of takeout and emails 
        """
        email_id = max(self._to_addr_dict, key=self._to_addr_dict.get)

        data = {"tbl_object": self.datasources_tbl,
                "name": email_id, 
                "source": self.__source__, "message": f"{email_count} emails"}


        store_datasource(**data)
        return 
        


    async def download_emails(self, loop, executor):
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

        self.email_count = 0

        _, _ = await asyncio.wait(
            fs=[loop.run_in_executor(executor,  
                functools.partial(self.save_email, message, number)) for (number, message) in enumerate(self.email_mbox)],
            return_when=asyncio.ALL_COMPLETED)


        # for message in self.email_mbox:
        #     #email_uid = self.emails[0].split()[x]

        #     email_from, email_to, subject, local_message_date, email_message = message["From"], \
        #         message["To"], message["Subject"], message["Date"], message
        #     await self.save_email(email_from, email_to, subject,
        #                     local_message_date, email_message)
            
        # logger.info(f"\n\nTotal number of emails {self.email_count}\n\n")
        
        
        self.__update_source_table(self.email_count)
        
       
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

    def save_email(self, email_message, number):
        email_from = email_message["From"]
        email_to = email_message["To"]
        subject = email_message["Subject"]
        local_message_date = email_message["Date"]

        self.__add_to_addr_address(email_to)

        message_type = email_message.get("X-Gmail-Labels")

        
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
                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    nbody = part.get_payload(decode=True)  # decode
                    body = body + self.handle_encoding(nbody)

                elif ctype == 'text/html' and 'attachment' not in cdispo:
                    # this is generally the same as text/plain but has
                    # html embedded into it. save it another file with
                    # html extension
                    hbody = part.get_payload(decode=True)  # decode
                    html_body = html_body + self.handle_encoding(hbody)

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
                            logger.error(
                                f" MIME type {ctype} with a file_name {attachment_name}")
                            extra_path = os.path.join(
                                self.extra_dir, attachment_name)
                            with open(extra_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments.append(extra_path)
                            
             
                        logger.info(
                            f"Ctype is {ctype} and attachment name is {attachment_name}")

                    else:
                        logger.error(
                            f"Mostly junk MIME type {ctype} without a file_name")


        else:
            # when the email is just plain text
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
                logger.error(e)
                logger.error(body)
                return

        email_text = self.get_clean_html(html_body)
        with open(file_path_html, "wb") as f:
            data = f"From: {email_from}{nl}To: {email_to}{nl}Date: {local_message_date}{nl}Attachments:{attachments}{nl}Subject: {subject}{nl}\nBody: {nl}{html_body}"
            f.write(data.encode())

        raw_id, message_id = self.__message_id(email_message)

        data = {"email_id": message_id, 
                "email_id_raw": raw_id,
                "from_addr" : email_from,
                "subject": subject,
                "to_addr": email_to,
                "content": email_text,
                "date": datetime.datetime.utcfromtimestamp(epoch),
                "path": file_path_html,
                "attachments": False,
                "message_type": message_type}
        

        if attachments:
            data.update({"attachments": True})

        self.store(attachments, data)
        # try:
        #     data.update({"tbl_object": self.email_table})
        #     store_email(**data)
        #     data.update({"tbl_object": self.indexed_email_content_tbl})
        #     content = data["content"] + data["subject"]
        #     data.update({"content": content})
            
        #     store_email_content(**data)
        
        #     data.update({"tbl_object": self.email_attachements_tbl})
        #     for attachment_path in attachments:
        #         data.update({"path": attachment_path, "attachment_name" :attachment_name.split("/")[-1]})
        #         store_email_attachment(**data)

        
        
        # except DuplicateEntryError as e:
        #     logger.error(e)


        

        #logger.error(f"{email_from} -- {email_to}")
        if attachments:
            logger.error(f"This is the attachement array {attachments}")
        self.email_count +=1 
        logging.info(f"The email count at this stage is {self.email_count} and the number is {number}")
        return

    def store(self, attachments, data):
        try:
            if attachments:
                data.update({"attachments": True})
                
            data.update({"tbl_object": self.email_table})
            store_email(**data)
            data.update({"tbl_object": self.indexed_email_content_tbl})
            content = data["content"] + data["subject"]
            data.update({"content": content})
            
            store_email_content(**data)
        
            data.update({"tbl_object": self.email_attachements_tbl})
            for attachment_path in attachments:
                data.update({"path": attachment_path, "attachment_name" :attachment_path.split("/")[-1]})
                store_email_attachment(**data)

        
        
        except DuplicateEntryError as e:
            logger.error(e)
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

