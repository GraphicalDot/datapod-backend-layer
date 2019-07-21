
#-*- coding: utf-8 -*-
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def convert_type(value):
    if isinstance(value, bytes):
        logging.error(f"{value} is in bytes")
        value = value.decode()
    return value


def store_credentials(credentials_tbl_obj, username, password_hash, id_token, access_token, refresh_token):

    

    try:
        user_id = (credentials_tbl_obj.insert(username=convert_type(username),  
                                    password_hash=convert_type(password_hash),
                                    id_token=convert_type(id_token), 
                                    access_token= convert_type(access_token), 
                                    refresh_token=convert_type(refresh_token))
           .on_conflict_replace()
           .execute())

        logger.info(f"On insert the credentials userid is {user_id}")
    except Exception as e:
        logger.error(f"Couldnt save data to credentials_tbl because of {e}")
    return 


def update_id_and_access_tokens(credentials_tbl_obj, username, id_token, access_token):
    try:
        credentials_tbl_obj.update(
            id_token=convert_type(id_token),  
            access_token= convert_type(access_token)).\
        where(credentials_tbl_obj.username==username).\
        execute()

        logger.info(f"On update al tokens the credentials userid is {username}")
    except Exception as e:
        logger.error(f"Couldnt save data to credentials_tbl because of {e}")
    return 


def update_mnemonic(credentials_tbl_obj, username, mnemonic, salt):
    try:
        credentials_tbl_obj.update(
            mnemonic=convert_type(mnemonic), 
            salt=convert_type(salt)).\
        where(credentials_tbl_obj.username==username).\
        execute()

        logger.info(f"On update mnemonic the credentials username is {username}")
    except Exception as e:
        logger.error(f"Couldnt update mnemonic for credentials_tbl because of {e}")
    return 

def update_password_hash(credentials_tbl_obj, username, password_hash):
    try:
        credentials_tbl_obj.update(
            password_hash=convert_type(password_hash)).\
        where(credentials_tbl_obj.username==username).\
        execute()

        logger.success(f"Password hash has been updated in the dataabse {username}")
    except Exception as e:
        logger.success(f"Password hash cant be updated in the dataabse because of error {e}")

    return 



def get_credentials(credentials_tbl_obj):
    try:
        for person in credentials_tbl_obj.select().dicts():
            for key, value in person.items():
                if isinstance(value, bytes):
                    person.update({key: value.decode()})
            return  person
    except Exception as e:
        logging.error(f"Couldnt fetch credentials data  {e}")
    return 



def update_datasources_status(datasources_tbl_obj, source, name, message):
    try:
        user_id = datasources_tbl_obj.insert(source=source,  
                                    name=name,
                                    message=message).on_conflict_replace().execute()

        logger.info(f"On insert new datasource is {source}")
    except Exception as e:
        logger.error(f"Couldnt new datasource source updated because of {e}")
    return 


def get_datasources_status(datasources_tbl_obj):
    """

    To get status of all the datasources that have been 
    fetched till now
    """
    try:
        return datasources_tbl_obj.select().dicts()
    
    except Exception as e:
        logging.error(f"Couldnt fetch credentials data  {e}")
    return 