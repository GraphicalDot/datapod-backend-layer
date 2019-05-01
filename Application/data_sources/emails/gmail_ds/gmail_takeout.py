
SERVER = "imap.gmail.com"
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
from  analysis.bank_statements import BankStatements
from  analysis.cab_service import CabService
import bleach

    db_instance = create_db_instance(app.config.db_dir_path)
    stored_value = get_key("logs", db_instance)

    value = [{"date": indian_time_stamp(), 
            "status": "success", 
            "message": "Facebook data has been parsed successfully"}]
    
    if stored_value:
        value = value+stored_value  

    #logger.info(f"value stored against logs is {value}")
    insert_key("logs", value, db_instance)

    insert_key("facebook_images", images, db_instance)


    stored_value = get_key("services", db_instance)
    logger.info("Stored value against services %s"%stored_value)

    #delete_key("services", db_instance)
    value = [{"time": indian_time_stamp(), 
            "service": "facebook", 
            "message": f"{len(images)} images present"}]
    
    if stored_value:
        
        for entry in stored_value:
            if entry.get("service") == "facebook":
                break
        stored_value.remove(entry)
        stored_value.extend(value)
    else:
        stored_value = value

    insert_key("services", stored_value, db_instance)

    close_db_instance(db_instance)


# import coloredlogs, verboselogs, logging
# verboselogs.install()
# coloredlogs.install()
# logger = logging.getLogger(__name__)
from database_calls.database_calls import create_db_instance, close_db_instance, get_key, insert_key
DEBUG=False
from asyncinit import asyncinit
import pytz
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def indian_time_stamp(naive_timestamp=None):
    tz_kolkata = pytz.timezone('Asia/Kolkata')
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp/1000.0))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp.strftime(time_format + " %Z%z")



class GmailsEMTakeout(object):

    def __init__(self, gmail_takeout_path, user_data_path, db_dir_path):
        self.db_dir_path = db_dir_path
        self.email_mbox = mailbox.mbox(gmail_takeout_path) 
        self.email_dir_txt = os.path.join(user_data_path, "mails/gmail/emails_txt")
        
        if not os.path.exists(self.email_dir_txt):
            logger.warning(f"Path doesnt exists creating {self.email_dir_txt}")
            os.makedirs(self.email_dir_txt) 


        self.email_dir_html = os.path.join(user_data_path, "mails/gmail/email_html")
        if not os.path.exists(self.email_dir_html):
            logger.warning(f"Path doesnt exists creating {self.email_dir_html}")
            os.makedirs(self.email_dir_html)


        self.image_dir = os.path.join(user_data_path, "mails/gmail/images")
        if not os.path.exists(self.image_dir):
            logger.warning(f"Path doesnt exists creating {self.image_dir}")
            os.makedirs(self.image_dir) 


        self.pdf_dir = os.path.join(user_data_path, "mails/gmail/pdfs")
        if not os.path.exists(self.pdf_dir):
            logger.warning(f"Path doesnt exists creating {self.pdf_dir}")
            os.makedirs(self.pdf_dir) 


        self.extra_dir = os.path.join(user_data_path, "mails/gmail/extra")
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

        """
        i = 0
        for message in self.email_mbox: 
            #email_uid = self.emails[0].split()[x]
            email_from, email_to, subject, local_message_date, email_message = message["From"], \
                    message["To"], message["Subject"], message["Date"], message
            self.save_email(email_from, email_to, subject, local_message_date, email_message)
            i += 1
            if i%100 == 0:
                logger.info(f"NUmber of emails saved {i}")
        logger.info(f"\n\nTotal number of emails {i}\n\n")
        """
        db_instance = create_db_instance(self.db_dir_path)
        stored_value = get_key("logs", db_instance)

        value = [{"date": indian_time_stamp(), 
                "status": "success", 
                "message": "Gmail takeout has been parsed successfully"}]
        
        if stored_value:
            value = value+stored_value  
    
        logger.info(f"value stored against logs is {value}")
        insert_key("logs", value, db_instance)
        close_db_instance(db_instance)
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
        sender_dir_name, sender_sub_dir_name = self.extract_email_from(email_from)
        self.ensure_directory(sender_dir_name, sender_sub_dir_name)

        epoch = self.convert_to_epoch(local_message_date)

        file_name_text = "email_" + str(epoch) + ".txt"
        file_name_html = "email_" + str(epoch) + ".html"
        #multipart/mixed,  multipart/alternative, multipart/related, text/html
        body = ""
        html_body = ""
        attachments = "\n"
        sender_sub_dir_txt = os.path.join(f"{self.email_dir_txt}/{sender_dir_name}", sender_sub_dir_name)

        file_path_text = os.path.join(sender_sub_dir_txt, file_name_text)
        
        
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
                            with open(os.path.join(self.image_dir, attachment_name), "wb") as f:
                                f.write(part.get_payload(decode=True))
                        elif ctype == "application/pdf" or ctype =="application/octet-stream":
                            with open(os.path.join(self.pdf_dir, attachment_name), "wb") as f:
                                f.write(part.get_payload(decode=True))

                        else:
                            logger.error(f" MIME type {ctype} with a file_name {attachment_name}")
                            with open(os.path.join(self.extra_dir, attachment_name), "wb") as f:
                                f.write(part.get_payload(decode=True))

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


        if isinstance(body, str):
            body = body.encode()
        
        text = self.remove_html(body)
        if isinstance(body, str):
            html_body = html_body.encode()


        with open(file_path_text, "wb") as f:
            data = f"From: {email_from}{nl}To: {email_to}{nl}Date: {local_message_date}{nl}Attachments:{attachments}{nl}Subject: {subject}{nl}\nBody: {nl}{text}"
            if DEBUG:
                logger.info(f"TEXT BODY {data}")
            f.write(data.encode())

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
    path ="/home/feynman/Downloads/takeout-20190418T154732Z-001/Takeout/Mail/All mail Including Spam and Trash.mbox"  
    instance = GmailsEMTakeout(path)
    instance.download_emails()
