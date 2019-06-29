#-*- coding: utf-8 -*-
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def store(tbl_obj, api_key, api_secret):
    try:
        tbl_obj.insert(exchange="binance",  
                        api_key=api_key,
                        api_secret=api_secret)\
            .on_conflict_replace()\
            .execute()

        logger.success(f"On insert the credentials for binance exchange")
    except Exception as e:
        logger.error(f"Couldnt save creds data for binanace exchange because of {e}")
    return 


def get_creds(tbl_obj):
    print (tbl_obj)
    try:
        res = tbl_obj.select().where(tbl_obj.exchange=="binance").get()
        return res.api_key, res.api_secret
    except Exception as e:
        logger.error(f"Couldnt fetch creds data for binanace exchange because of {e}")
    return 