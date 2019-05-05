


from os import listdir
from os import path, getcwd, makedirs
from PyPDF2 import PdfFileReader, PdfFileWriter
import camelot
import hashlib
from analytics import Analytics

def decrypt_pdf(input_path, output_path, password):
    with open(input_path, 'rb') as input_file, \
        open(output_path, 'wb') as output_file:
        reader = PdfFileReader(input_file)
        reader.decrypt(password)

        writer = PdfFileWriter()

        for i in range(reader.getNumPages()):
            writer.addPage(reader.getPage(i))

        writer.write(output_file)
    return 

class HDFCBank(object):
    def __init__(self, pdf_password, pdf_folder_path):
        """
        Args:
            Password to open PDF file for hdfc bank, This is generally the 
                Customer id of the user
        
            pdf_folder_path 
                Path for the pdf folder it could be dowloaded 
                from any gmail client 
        
        """
        self.pdf_password = pdf_password
        self.pdf_folder_path = pdf_folder_path
        self.file_names = []
        self.analysis = {}

        self.temp_dir = path.join(path.dirname(getcwd()), "temp")
        if not path.exists(self.temp_dir):
            makedirs(self.temp_dir)

        pass

    @staticmethod
    def is_hdfc(subject):
        #TODO, only the emails received from hdfc bak should be counted

        """
        Find out from the email subject if this pdf is from HDFC bank
        """
        if subject.lower().find("hdfc") != -1:
            return True
        return 

    def collect_pdfs(self):
        """
        Args:
        Return :
            array of pdf file name which belongs to 
        
        Open the folder, and filter out the PDF which belongs to 
        HDFC bank

        """
        all_files = [f for f in listdir(self.pdf_folder_path) \
                    if path.isfile(path.join(self.pdf_folder_path, f))]

        self.file_names = [path.join(self.pdf_folder_path, filename) for filename in\
                         all_files if filename.startswith("hdfcbank")]
        print (self.file_names)
        return 

    def decrypt_pdfs(self):
        [decrypt_pdf(filename, path.join(self.temp_dir, path.basename(filename)), self.pdf_password) for filename in self.file_names]
        return 

    def analyse(self):
        """

        """
        self.collect_pdfs() ##collect all the pdf with hdfc bank
        self.decrypt_pdfs() ##decrpt the pdf files and save them in a temporary folder 
        ##Decrypting all the file with password and save it on the temporary folder 
        data = []
        for filename in [f for f in listdir(self.temp_dir) \
                    if path.isfile(path.join(self.pdf_folder_path, f))]:
            
            try:
                data += self.analyse_file(filename)
            except Exception as e:
                print (f"THis file couldnt be parsed {filename}")
        
        
        return data

    def analyse_file(self, filename):
        """
        While reading the file the first row will be 
        ['Date', 'Narration', 'Chq. / Ref No.', 'Value Date', 'Withdrawal Amount', 'Deposit Amount', 'Closing Balance*']
        We will split the date and will add two new columns, the first one will be the month 
        and second will be the year like 01 and 2018, 
        the first column will be the hash of the narration

        Return colums will be 
        [month, year, hash_narration, narration, 'Chq. / Ref No.', 'Value Date', 'Withdrawal Amount', 'Deposit Amount', 'Closing Balance*']

        Withdrwal amount will be reffered to as debit
        Deposit amount will be reffered to as credit
        """
        print(f"Reading file {filename}")
        pdf_reader = camelot.read_pdf(path.join(self.temp_dir, filename), pages="all")
        data = []
        pages  = 0
        while True:
            try:
                data += pdf_reader[pages].data   
            except: 
                break
            pages+= 1

        ##since we require only the month wise analysis, lets remove the dates and 
        ##keep only the month and year, now instead of first column, 
        ##we will have two columns in the beginning, the first one will be month
        #second one will be the year and so on.

        
        clean_data = [(e[0].split("/")[1], e[0].split("/")[2],  hashlib.sha3_224("".join(e).encode()).hexdigest(), 
                                e[1], e[2], e[3], e[4], e[5], e[6])
         for e in data[1:]]
        
        print (f"Headers of the file is {data[0]}")
        print(f"Length of the data is {len(clean_data)}\n")
        return clean_data


    def clean(self):
        """
        deletes the temporary folder which has the decrypted files 
        """
        pass


if __name__=="__main__":
    from pprint import pprint
    instance =  HDFCBank("35276617", "/home/feynman/Programs/datapod-backend-layer/Application/userdata/mails/gmail/pdfs")
    data = instance.analyse()
    pprint(data)
    i = 0
    for e in data:
        i += 1
        if len(e) != 9:
            print (e)

