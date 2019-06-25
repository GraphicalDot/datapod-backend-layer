#-*- coding: utf-8 -*-


import json
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def store_purchase(tbl_object, purchase):
    """
    purchases: a list of purchases dict
    """
    try:
        products = json.dumps(purchase["products"])
        tbl_object.insert(merchant_name=purchase["merchant_name"],  
                                    products=products, 
                                    source= purchase["source"], 
                                    time=purchase["time"]).execute()

        logger.info(f"On insert the purchase for  {purchase['merchant_name']}")
    except Exception as e:
        logger.error(f"Couldnt save purchase data {purchase}  because of {e}")
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
    logging.info(db_purchase_obj)
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
        logging.error(f"Couldnt fetch credentials data  {e}")
    return 
