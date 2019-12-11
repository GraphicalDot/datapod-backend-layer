
#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import aiomisc
#@retry(stop=stop_




@aiomisc.threaded
def get_credentials(credential_table):
    logger.info("Get credentials called")
    return credential_table.select().dicts()





@aiomisc.threaded
def insert_backup_entry(backup_list_table, disk_space_used, status, type, name):
    try:
        backup_list_table.insert(status=status,
                                    disk_space_used = disk_space_used,
                                    type=type,
                                    name=name
                                    ).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt insert backup entry {name} updated because of {e}")
    return 

@aiomisc.threaded
def update_status(status_table, datasource_name, username, status):
    try:
        status_table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")
        status_table.update(
                        status=status).\
                    where(status_table.username==username).\
                    execute()


    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 


@aiomisc.threaded
def update_percentage(status_table, username, percentage):
    status_table.update(
                percentage=percentage, 
                last_updated=datetime.datetime.now()).\
            where(status_table.username==username).\
            execute()
    return 


@aiomisc.threaded
def get_backup_list(tbl_object):

    result = tbl_object\
            .select()\
                
    
    return result

@aiomisc.threaded
def delete_status(status_table, datasource_name, username):
    try:
        status_table.delete().where(status_table.username==username).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt delete {datasource_name} updated because of {e}")
    return 


@aiomisc.threaded
def delete_archive(archives_table, checksum):
    try:
        archives_table.delete().where(archives_table.checksum==checksum).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt delete {checksum} from archives table because of {e}")
    return 

@aiomisc.threaded
def update_stats(stats_table, data_items, size, sync_frequency, sync_type, next_sync):
    """

    """
    try:
        stats_table.insert(
                data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).execute()
                                    
    except IntegrityError as e:
        logger.error(f"Couldnt insert stats for  {datasource_name} because of {e} so updating it")

        stats_table.update(
                            data_items = data_items,
                disk_space_used = size).\
        where(stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 





@aiomisc.threaded
def get_status(facebook_status_table, username=None):
    logger.info(f"This is the username {username}")
    if not username:
        return facebook_status_table.select().dicts()
    return facebook_status_table.select().where(facebook_status_table.username==username).dicts()
                                

@aiomisc.threaded
def get_stats(stats_table):
    return stats_table.select().dicts()
        

@aiomisc.threaded
def update_mnemonic_n_address(user_table, username, mnemonic, address, private_key):
    try:
        user_table.update(
            mnemonic=mnemonic,  
            address= address,
            encryption_key=private_key).\
        where(user_table.username==username).\
        execute()

        logger.debug(f"Credentials user table updated with mnemonic and address")
    except Exception as e:
        logger.error(f"Credentials user table coudlnt be updated with mnemonic and address because of {e}")
    return 