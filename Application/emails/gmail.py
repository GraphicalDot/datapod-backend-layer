 

SERVER = "imap.gmail.com"
from pprint import pprint
import datetime
import email
import imaplib
import mailbox
import os, sys
import base64

path = os.path.dirname(os.path.realpath(os.getcwd()))

print (path)

sys.path.append(path)
from  analysis.bank_statements import BankStatements
from  analysis.cab_service import CabService



import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__name__)

DEBUG=False

# result, data = mail.uid('search', None, "UNSEEN") # (ALL/UNSEEN)
# i = len(data[0].split())

# for x in range(i):
#     latest_email_uid = data[0].split()[x]
#     result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
#     # result, email_data = conn.store(num,'-FLAGS','\\Seen') 
#     # this might work to set flag to seen, if it doesn't already
#     raw_email = email_data[0][1]
#     raw_email_string = raw_email.decode('utf-8')
#     email_message = email.message_from_string(raw_email_string)

#     # Header Details
#     date_tuple = email.utils.parsedate_tz(email_message['Date'])
#     if date_tuple:
#         local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
#         local_message_date = "%s" %(str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
#     email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
#     email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
#     subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))

#     # Body details
#     for part in email_message.walk():
#         body = part.get_payload(decode=True)
#         file_name = f"From:[{email_from}]To:[{email_to}]Date:[{local_message_date}]Subject:[{subject}]UID:[{str(x)}]"
#         output_file = open(file_name, 'w')
#         output_file.write(body.decode('utf-8'))
#         output_file.close()





class GmailEm(object):

    def __init__(self, server_name, inbox_type=None, mail_type=None):
        self.server_name = server_name
        self.items = None
        if not inbox_type:
            self.inbox_type = "inbox"

        if not mail_type:
            self.mail_type = "ALL"
    
        self.email_dir_txt = os.path.join(os.path.dirname(os.getcwd()), "user_data/mails/gmail/emails_txt")
        if not os.path.exists(self.email_dir_txt):
            os.makedirs(self.email_dir_txt) 

        self.email_dir_html = os.path.join(os.path.dirname(os.getcwd()), "user_data/mails/gmail/email_html")
        if not os.path.exists(self.email_dir_html):
            os.makedirs(self.email_dir_html)

        self.image_dir = os.path.join(os.path.dirname(os.getcwd()), "user_data/mails/gmail/images")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir) 

        self.pdf_dir = os.path.join(os.path.dirname(os.getcwd()), "user_data/mails/gmail/pdfs")
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir) 

        self.extra_dir = os.path.join(os.path.dirname(os.getcwd()), "user_data/mails/gmail/extra")
        if not os.path.exists(self.extra_dir):
            os.makedirs(self.extra_dir) 
        logger.info("App intiation been done")

    def connect(self, username, password):
        self.mail_instance = imaplib.IMAP4_SSL(self.server_name)
        self.mail_instance.login(username, password)
        self.mail_instance.list()
        self.mail_instance.select(self.inbox_type)
        logger.info("COnnected successffuly")


    def fetch_email_ids(self):
        result, self.emails = self.mail_instance.uid('search', None, self.mail_type) # (ALL/UNSEEN)
        if result != "OK":
            logger.error("Couldnt log into the mail server")
            raise Exception("Couldnt log into the mail server")

    def download_emails(self):
        """
        Downloding list of emails from the gmail server
        """
        logger.info("Executing download emails")

        self.fetch_email_ids()
        i = len(self.emails[0].split())
        logger.info(f"NUmber of emails is {i}")

        #TODO: remove indexing on list
        for x in range(i):
            email_uid = self.emails[0].split()[x]
            email_from, email_to, subject, local_message_date, email_message = self.download_email(email_uid)
            self.save_email(email_uid, email_from, email_to, subject, local_message_date, email_message)
        return 


    def download_email(self, email_uid):
        """
        Download a particular email
        """
        # this might work to set flag to seen, if it doesn't already
        result, email_data = self.mail_instance.uid('fetch', email_uid, '(RFC822)')

        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        # Header Details
        date_tuple = email.utils.parsedate_tz(email_message['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            local_message_date = "%s" %(str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
        else:
            local_message_date = None

        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))

        return email_from, email_to, subject, local_message_date, email_message


    def prefix_attachment_name(self, filename, email_uid, email_subject, email_from):
        if BankStatements.is_bank_statement(email_subject):
            prefix = BankStatements.which_bank(email_subject)

        elif CabService.is_cab_service(email_subject):
            prefix = CabService.which_cab_service(email_from, email_subject)

        else:
            prefix = "UNKNOWN"

        return f"{prefix}_{email_uid}_{filename}"


    def save_email(self, email_uid, email_from, email_to, subject, local_message_date, email_message):
        # Body details
        logger.info(f"email_uid={email_uid}, email_from={email_from}, email_to={email_to}, subject={subject}, local_message_date={local_message_date}")
        
        if isinstance(email_uid, bytes):
            email_uid = email_uid.decode()

        file_name_text = "email_" + email_uid + ".txt"
        file_name_html = "email_" + email_uid + ".html"
        #multipart/mixed,  multipart/alternative, multipart/related, text/html
        body = ""
        html_body = ""
        attachments = "\n"
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()
                if DEBUG:
                    logger.error(f"This is the ctype {ctype}")
                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    nbody = part.get_payload(decode=True)  # decode
                    body = body + nbody.decode()

                elif ctype == 'text/html' and 'attachment' not in cdispo:
                    ##this is generally the same as text/plain but has 
                    ##html embedded into it. save it another file with 
                    ##html extension
                    hbody = part.get_payload(decode=True)  # decode
                    html_body = html_body + hbody.decode()

                else:
                    ##most of the times, this code block will have junk mime 
                    ##type except the attachment part 

                    if part.get_filename():
                        #attachment_name = part.get_filename() + "__"+ str(email_uid)
                        ##prefix attachment with TAGS like BANK, CAB, 
                        attachment_name = self.prefix_attachment_name(
                                part.get_filename(), email_uid, subject, email_from)


                        if ctype.startswith("image"):
                            with open(os.path.join(self.image_dir, attachment_name), "wb") as f:
                                f.write(part.get_payload(decode=True))
                        elif ctype == "application/pdf":
                            with open(os.path.join(self.pdf_dir, attachment_name), "wb") as f:
                                f.write(part.get_payload(decode=True))

                        else:
                            with open(os.path.join(self.extra_dir, attachment_name), "wb") as f:
                                f.write(part.get_payload(decode=True))

                        logger.info(f"Attachment with name {attachment_name} and content_type {ctype} found")            

                        attachments += f"{attachment_name}\n"
                    else:
                        if DEBUG:
                            logger.error(f"Mostly junk MIME type {ctype} without a file_name")


            if DEBUG:
                # not multipart - i.e. plain text, no attachments, keeping fingers crossed
                pprint(body)

        else:
            #when the email is just plain text
            body = part.get_payload(decode=True)
            logger.error("email with Plaintext found, Which is rare")

        file_path_text = os.path.join(self.email_dir_txt, file_name_text)
        file_path_html = os.path.join(self.email_dir_html, file_name_html)

        nl = "\r\n"
        with open(file_path_text, "wb") as f:
            data = f"From: {email_from}{nl}To: {email_to}{nl}Date: {local_message_date}{nl}Attachments:{attachments}{nl}Subject: {subject}{nl}\nBody: {nl}{body.encode()}"
            if DEBUG:
                logger.info(f"TEXT BODY {data}")
            f.write(data.encode())

        with open(file_path_html, "wb") as f:
            data = f"From: {email_from}{nl}To: {email_to}{nl}Date: {local_message_date}{nl}Attachments:{attachments}{nl}Subject: {subject}{nl}\nBody: {nl}{html_body.encode()}"
            if DEBUG:
                logger.info(f"HTML BODY {data}")
            f.write(data.encode())


        logger.info("\n")
        return 


    def old_save_email(self, email_uid, email_from, email_to, subject, local_message_date, email_message):
        # Body details
        """
        logger.info(f"email_uid={email_uid}, email_from={email_from}, email_to={email_to}, subject={subject}, local_message_date={local_message_date}")
        for part in email_message.walk():
            
            body = part.get_payload(decode=True)

            if part.get_content_maintype() == 'multipart':
            
                logger.info(body)
                continue
            if part.get('Content-Disposition') is None:
                logger.warning(f"CONTENT Dispostion is {part.get('Content-Disposition')}")
                continue


            body = part.get_payload(decode=True)
            content_type= part.get_content_type()
            file_name = "email_" + str(email_uid) + ".txt"

            j_file_name = f"From:[{email_from}]Date:[{local_message_date}]UID:[{str(email_uid)}Content-type:[{content_type}]]"
            
            file_path = os.path.join(self.email_dir, file_name)
            logger.info(f"J_Filepath {j_file_name}")
            
            
            attachment_name = part.get_filename()
            if attachment_name:
                
            
            logger.info(f"Attachment in the email name is  {attachment_name}")

            output_file = open(file_path, 'w')
            if body:
                output_file.write("From: %s\nTo: %s\nDate: %s\nSubject: %s\n\nBody: \n\n%s" %(email_from, email_to,local_message_date, subject, base64.b64encode(body)))
                logger.info(f"Body was parsed for {email_uid}")
            else:
                logger.error(f"Body couldnt be parsed for {email_uid}")
                output_file.write("From: %s\nTo: %s\nDate: %s\nSubject: %s\n\nBody: \n\n%s" %(email_from, email_to,local_message_date, subject, "Body coudlnt be parsed"))

            output_file.close()
        logger.info("\n")
        """
        return 

if __name__ == "__main__":
    logger.error("App started")
    email_instance = GmailEm(SERVER)
    email_instance.connect("dummy.houzier.saurav@gmail.com", "Groot1234#")
    email_instance.download_emails()
    logger.info("App Ended")
