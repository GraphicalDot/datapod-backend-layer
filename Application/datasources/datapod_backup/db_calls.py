
#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import aiomisc
#@retry(stop=stop_








@aiomisc.threaded
def update_status(status_table,status, checksum=None, path=None, percentage=None):
    try:
        status_table.insert(status=status,
                                    path = path,
                                    checksum=checksum,
                                    percentage=percentage
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {checksum} because of {e} so updating it")

        logger.error(f"Couldnt insert {checksum} because of {e} so updating it")

        if path:
            status_table.update(
                status=status, 
                path = path,
                ).\
            where(status_table.checksum==checksum).\
            execute()
      
        else:
            status_table.update(
                            status=status).\
                        where(status_table.checksum==checksum).\
                        execute()


    except Exception as e:
        logger.error(f"Couldnt Backup {checksum} updated because of {e}")
    return 

@aiomisc.threaded
def update_percentage(status_table, checksum, percentage):
    status_table.update(
                percentage=percentage, 
                last_updated=datetime.datetime.now()).\
            where(status_table.checksum==checksum).\
            execute()
    return 


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
        