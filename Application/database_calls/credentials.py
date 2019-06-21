
#-*- coding: utf-8 -*-
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def store_credentials(credentials_tbl_obj, username, password_hash, id_token, access_token, refresh_token):
    try:
        user_id = (credentials_tbl_obj.insert(username=username,  
                                    password_hash=password_hash,
                                    id_token=id_token, 
                                    access_token= access_token, 
                                    refresh_token=refresh_token)
           .on_conflict_replace()
           .execute())

        logger.info(f"On insert the credentials userid is {user_id}")
    except Exception as e:
        logger.error(f"Couldnt save data to credentials_tbl because of {e}")
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
