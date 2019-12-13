import aiomisc
#@retry(stop=stop_after_attempt(2))
import json
import datetime
from peewee import IntegrityError, OperationalError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import os



@aiomisc.threaded
def delete_all_plugin_permissions(permission_table, plugin_name):
    try:
        permission_table.delete().where(permission_table.plugin_name==plugin_name).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt delete {plugin_name} permissions because of {e}")
    return 



@aiomisc.threaded
def delete_plugin_permission(permission_table, plugin_name, table_name):
    try:
        permission_table.delete().where(permission_table.plugin_name==plugin_name, permission_table.table_name==table_name ).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt delete {plugin_name} permission for {table_name}  because of {e}")
    return 



@aiomisc.threaded
def get_permissions(table, plugin_name):
    return table.select().where(table.plugin_name==plugin_name).dicts()
        

@aiomisc.threaded
def get_table_names(table):
    return table.select().dicts()

@aiomisc.threaded
def store_permission(**data):
    """
    purchases: a list of purchases dict
    """
    permission_table = data["tbl_object"]

    try:
        permission_table.insert(plugin_name=data["plugin_name"], 
                        datasource_name=data["datasource_name"],
                           table_name = data["table_name"],
                        ).execute()

        #logger.success(f"Success on insert indexed content for  email_id --{data['email_id']}-- ")


    except Exception as e:
        logger.error(f"Error on inserting permission for {data['plugin_name']} {data['datasource_name']} with error {e}")
    return



def store_table_names(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    try:
        table.insert( datasource_name=data["datasource_name"],
                           table_name = data["table_name"],
                           display_name = data["display_name"]
                        ).execute()

        #logger.success(f"Success on insert indexed content for  email_id --{data['email_id']}-- ")


    except Exception as e:
        logger.error(f"Error on inserting permission for {data['table_name']} {data['datasource_name']} with error {e}")
    return



