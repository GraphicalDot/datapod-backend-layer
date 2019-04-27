


from .hdfc_bank import HDFCBank

class BankStatements(object):


    @staticmethod
    def is_bank_statement(subject):
        if subject.lower().find("account statement") != -1:
            return True
        return False

    @staticmethod
    def which_bank(subject):
        if HDFCBank.is_hdfc(subject):
            return "BANK_HDFC"
        else:
            return "BANK_UKNOWN"




