#-*- coding: utf-8 -*-

from tenacity import *
import peewee
import json
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)


@retry(stop=stop_after_attempt(2))
def store(tbl_object, merchant_name, source, time, dest, src):
    """
    purchases: a list of purchases dict
    """

    try:
        tbl_object.insert(merchant_name=merchant_name,  
                            src= src,
                            dest=dest,
                            source=source, 
                            time=time).execute()

        logger.info(f"On insert the reservations for  {merchant_name}")
    except peewee.OperationalError  as e:
        logger.error(f"RESERVATIONS: Couldnt save reservations data {merchant_name}  because of {e}")
        raise 

    except peewee.IntegrityError as e:
        logger.error(f"RESERVATIONS: Duplicate key exists {merchant_name}  because of {e}")

    return 



def filter_merchant_name(tbl_object, page, number,  merchant_name=None):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    if merchant_name:
        return tbl_object\
                .select()\
                .where(tbl_object.merchant_name == merchant_name)\
                .order_by(-tbl_object.time)\
                .paginate(page, number)\
                .dicts()
    else:
        return tbl_object\
                .select()\
                .order_by(-tbl_object.time)\
                .paginate(page, number)\
                .dicts()


