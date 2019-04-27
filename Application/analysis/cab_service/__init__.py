


from .uber_cab_service import UberCabService

class CabService(object):


    @staticmethod
    def is_cab_service(subject):
        ##TODO: trip might be a train or Flight trip
        ##solve this
        if subject.lower().find("trip") != -1:
            return True
        return False

    @staticmethod
    def which_cab_service(email_from, subject):
        if UberCabService.is_uber_cab(email_from, subject):
            return "CAB_UBER"
        else:
            return "CAB_UNKNOWN"