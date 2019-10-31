#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import aiomisc
#@retry(stop=stop_after_attempt(2))


@aiomisc.threaded
def update_status(facebook_status_table, datasource_name, username, status):
    try:
        facebook_status_table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        facebook_status_table.update(
            status=status).\
        where(facebook_status_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 


@aiomisc.threaded
def update_stats(facebook_stats_table, datasource_name, username, data_items, size, sync_frequency, sync_type, next_sync):
    """

    """
    try:
        facebook_stats_table.insert(
                source = datasource_name,
                username = username,
                data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).execute()
                                    
    except IntegrityError as e:
        logger.error(f"Couldnt insert stats for  {datasource_name} because of {e} so updating it")

        facebook_stats_table.update(
                            data_items = data_items,
                disk_space_used = size).\
        where(facebook_stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 




@aiomisc.threaded
def get_status(facebook_status_table):
    return facebook_status_table.select().dicts()
                                    


@aiomisc.threaded
def get_stats(facebook_stats_table):
    return facebook_stats_table.select().dicts()
        


def store_creds(tbl_object, username, password):
    """
    purchases: a list of purchases dict
    """


    try:
        tbl_object.insert(
                    username = username,
                    password=password).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
   
    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Github creds data insertion failed {username} with {e}")
    return 


@aiomisc.threaded
def logout(credentials_tbl_obj):
    try:
        credentials_tbl_obj.delete().execute()
        logger.info("Flushing creds table")
    except Exception as e:
        logger.error(f"Couldntflush credentials_tbl because of {e}")
        raise 
    return 


def get_credentials(credential_table):
    return credential_table.select().dicts()



@aiomisc.threaded
def store_credentials(credentials_tbl_obj, username, password_hash, id_token, access_token, refresh_token, name, email):

    try:
        credentials_tbl_obj.insert(username=username,  
                                        password_hash=password_hash,
                                        id_token=id_token, 
                                        access_token= access_token, 
                                        refresh_token=refresh_token,
                                        name = name, 
                                        email=email
                                        ).execute()
        

    except IntegrityError:
        logger.info(f"Credentials for the user already exists, updating it now")
        credentials_tbl_obj.update(
                            id_token=id_token, 
                            access_token= access_token, 
                            refresh_token=refresh_toke)
                        ).\
                    where(credentials_tbl_obj.username==username).\
                    execute()

    except Exception as e:
        logger.error("Saving credentials of the users failed {e}")
        raise APIBadRequest("Could save credentials because of {e.__str__()}")


    return 


@aiomisc.threaded
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
