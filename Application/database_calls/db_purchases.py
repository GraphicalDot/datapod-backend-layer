#-*- coding: utf-8 -*-

#from tenacity import *
import peewee
import json
from loguru import logger
from utils.utils import async_wrap

#@retry(stop=stop_after_attempt(2))
@async_wrap
def store(tbl_object, products, merchant_name, source, time):
    """
    purchases: a list of purchases dict
    """
    try:
        products = json.dumps(products)
        tbl_object.insert(merchant_name=merchant_name,  
                                    products=products, 
                                    source=source, 
                                    time=time).execute()
        logger.info(f"On insert the purchase for  {merchant_name}")
    except peewee.OperationalError  as e:
        logger.error(f"PURCHASES: Couldnt save purchase data {merchant_name}  because of {e}")
    
    except peewee.IntegrityError as e:
        logger.error(f"PURCHASES: Duplicate key exists {merchant_name}  because of {e}")
    
    return 


def update_id_and_access_tokens(credentials_tbl_obj, username, id_token, access_token):
    try:
        credentials_tbl_obj.update(
            id_token=id_token,  
            access_token= access_token).\
        where(credentials_tbl_obj.username==username).\
        execute()

        logger.info(f"On update al tokens the credentials userid is {username}")
    except Exception as e:
        logger.error(f"Couldnt save data to credentials_tbl because of {e}")
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


def format(config, db_purchase_obj):
    """
    db_purchase_obj: retrived from the db
    """
    logger.info(db_purchase_obj)
    products = json.loads(db_purchase_obj["products"])
    return {
            "merchant_name": db_purchase_obj["merchant_name"],
            "products": products,
            "time": db_purchase_obj["time"]
    }



def update_mnemonic(credentials_tbl_obj, username, mnemonic):
    try:
        credentials_tbl_obj.update(
            mnemonic=mnemonic).\
        where(credentials_tbl_obj.username==username).\
        execute()

        logger.info(f"On update mnemonic the credentials username is {username}")
    except Exception as e:
        logger.error(f"Couldnt update mnemonic for credentials_tbl because of {e}")
    return 


def get_credentials(credentials_tbl_obj):
    try:
        for person in credentials_tbl_obj.select().dicts():
            return person
    except Exception as e:
        logger.error(f"Couldnt fetch credentials data  {e}")
    return 
