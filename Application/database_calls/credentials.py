
#-*- coding: utf-8 -*-

from loguru import logger
from peewee import IntegrityError
from errors_module.errors import APIBadRequest

def convert_type(value):
    if isinstance(value, bytes):
        logger.error(f"{value} is in bytes")
        value = value.decode()
    return value

def logout(credentials_tbl_obj):
    try:
        credentials_tbl_obj.delete().execute()
        logger.info("Flushing creds table")
    except Exception as e:
        logger.error(f"Couldntflush credentials_tbl because of {e}")
        raise 
    return 

def store_credentials(credentials_tbl_obj, username, password_hash, id_token, access_token, refresh_token, name, email):
    person  = get_credentials(credentials_tbl_obj)
    
    if person["username"] != username:
        raise Exception("Different usernames on same Application arent allowed")
    
    try:
        credentials_tbl_obj.insert(username=convert_type(username),  
                                        password_hash=convert_type(password_hash),
                                        id_token=convert_type(id_token), 
                                        access_token= convert_type(access_token), 
                                        refresh_token=convert_type(refresh_token),
                                        name = name, 
                                        email=email
                                        ).execute()
        

    except IntegrityError:
        logger.info(f"Credentials for the user already exists, updating it now")
        credentials_tbl_obj.update(
                            id_token=convert_type(id_token), 
                            access_token= convert_type(access_token), 
                            refresh_token=convert_type(refresh_token)
                        ).\
                    where(credentials_tbl_obj.username==username).\
                    execute()

    except Exception as e:
        logger.error("Saving credentials of the users failed {e}")
        raise APIBadRequest("Could save credentials because of {e.__str__()}")


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


def update_mnemonic(credentials_tbl_obj, username, mnemonic, salt, address, encryption_key):
    try:
        credentials_tbl_obj.update(
            mnemonic=convert_type(mnemonic), 
            salt=convert_type(salt),
            address=convert_type(address),
            encryption_key=convert_type(encryption_key),
            ).\
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
    res = credentials_tbl_obj.select().dicts()

    logger.info(f"Number of entries in creds table is {len(res)}")
    try:
        for person in credentials_tbl_obj.select().dicts():
            for key, value in person.items():
                if isinstance(value, bytes):
                    person.update({key: value.decode()})
            return  person
    except Exception as e:
        logger.error(f"Couldnt fetch credentials data  {e}")
    return 


def update_datasources_status(tbl_object, source, name, code, message, status):
    try:
        tbl_object.insert(source=source,  
                                    name=name,
                                    code=code,
                                    status=status,
                                    message=message).execute()
                                    

        logger.info(f"On insert new datasource is {source}")
    
    except IntegrityError as e:
        logger.error(f"Couldnt insert datasource source because of {e} so updating it")

        tbl_object.update(
            status=status,
            name=name,
            message=message).\
        where(tbl_object.source==source).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt new datasource source updated because of {e}")
    return 


def datasource_status(datasources_tbl_obj, code):
    return datasources_tbl_obj.select().where(datasources_tbl_obj.code == code).dicts()


def get_datasources_status(datasources_tbl_obj):
    """

    To get status of all the datasources that have been 
    fetched till now
    """
    return datasources_tbl_obj.select().dicts()
    
    