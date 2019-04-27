



from os import listdir
from os.path import isfile, join


class UberCabService(object):
    def __init__(self, pdf_folder_path):
        """
        Args:
            pdf_folder_path 
                Path for the pdf folder it could be dowloaded 
                from any gmail client 
        
        """
        self.pdf_folder_path = pdf_folder_path
        pass

    @staticmethod
    def is_uber_cab(email_from, subject):
        """
        Find out from the email subject if this pdf is from HDFC bank
        """
        if email_from.lower().find("uber") != -1:
            if subject.lower().find("trip with uber") != -1:
                return True
        return False

    def collect_pdfs(self):
        """
        Args:
        Return :
            array of pdf file name which belongs to 
        
        Open the folder, and filter out the PDF which belongs to 
        HDFC bank

        """
        all_files = [f for f in listdir(self.pdf_folder_path) \
                    if isfile(join(self.pdf_folder_path, f))]

        return [filename for filename in all_files if filename.lower().find("hdfc")]
