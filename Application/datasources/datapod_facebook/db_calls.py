#-*- coding: utf-8 -*-

import json
import datetime
from peewee import IntegrityError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger
import aiomisc
#@retry(stop=stop_after_attempt(2))


@aiomisc.threaded
def update_status(facebook_status_table, datasource_name, username, status, path=None, original_path=None):
    try:
        facebook_status_table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    path = path,
                                    original_path=original_path
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        if path and original_path:
            facebook_status_table.update(
                status=status, 
                path = path,
                original_path=original_path).\
            where(facebook_status_table.username==username).\
            execute()
        elif original_path:
            facebook_status_table.update(
                            status=status, 
                            original_path=original_path).\
                        where(facebook_status_table.username==username).\
                        execute()

        elif path:
            facebook_status_table.update(
                            status=status, 
                            path=path).\
                        where(facebook_status_table.username==username).\
                        execute()
        else:
            facebook_status_table.update(
                            status=status).\
                        where(facebook_status_table.username==username).\
                        execute()


    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 

@aiomisc.threaded
def delete_status(status_table, datasource_name, username):
    try:
        status_table.delete().where(status_table.username==username).execute()
                                    

    except Exception as e:
        logger.error(f"Couldnt delete {datasource_name} updated because of {e}")
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
def get_status(facebook_status_table, username=None):
    logger.info(f"This is the username {username}")
    if not username:
        return facebook_status_table.select().dicts()
    return facebook_status_table.select().where(facebook_status_table.username==username).dicts()
                                

@aiomisc.threaded
def get_stats(facebook_stats_table):
    return facebook_stats_table.select().dicts()
        


@aiomisc.threaded
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
def store_image(**data):
    """
    purchases: a list of purchases dict
    """

    
    
    table = data["tbl_object"]
    if data.get("comments"):
        comments = json.dumps(data["comments"])
    else:
        comments = None

    if data.get("media_metadata"):
        media_metadata =  json.dumps(data["media_metadata"])
    else:
        media_metadata = None


    try:
        table.insert(
                    title = data["title"],
                    comments = comments,
                    media_metadata = media_metadata,
                    uri = data["uri"],
                    creation_timestamp = data.get("creation_timestamp"),
                    username = data.get("username"),
                    checksum=data.get("checksum"),
                    chat_image = data.get("chat_image"),
                    file_extension = data.get("file_extension"),
                    ).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f'Duplicate key present --{data.get("uri")}-- in table --FBdata-- {e}')
        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"facebook image data insertion failed {data.get('uri')} with {e}")
    return 



@aiomisc.threaded
def store_chats(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["chat_table"]
    try:
        table.insert(
                    username = data.get("username"),
                    checksum=data.get("checksum"),
                    title = data["title"],
                    participants = data["participants"],
                    messages = data["messages"],
                    thread_type = data["thread_type"],
                    timestamp = data["timestamp"],
                    message_content= data["message_content"],
                    chat_type = data["chat_type"],
                    chat_id = data["chat_id"],
                    chat_path = data["chat_path"]
                    ).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f'Duplicate key present --{data.get("chat_id")}-- in table --FBchat-- {e}')
        table.update(
                    checksum=data.get("checksum"),
                    title = data["title"],
                    participants = data["participants"],
                    messages = data["messages"],
                    message_content= data["message_content"],
                    chat_id = data["chat_id"],
                    ).where(table.chat_id==data["chat_id"]).execute()
        
        
        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"facebook image data insertion failed {data.get('chat_id')} with {e}")
    return 

@aiomisc.threaded
def store_address(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["table"]
    try:
        table.insert(
                    username = data.get("username"),
                    checksum=data.get("checksum"),
                    name=data.get("name"),
                    email=data.get("email"),
                    phone_number=data.get("phone_number"),
                    created_timestamp=data.get("created_timestamp"),
                    updated_timestamp=data.get("updated_timestamp")
                    ).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f'Duplicate key present --{data.get("chat_id")}-- in table --FBchat-- {e}')
        table.update(
                    checksum=data.get("checksum"),
                    email=data.get("email"),
                    phone_number=data.get("phone_number"),
                    created_timestamp=data.get("created_timestamp"),
                    updated_timestamp=data.get("updated_timestamp")
                    ).where(table.username==data["username"]).execute()
        
        
        #raise DuplicateEntryError(data['name'], "GithubRepo")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"facebook image data insertion failed {data.get('chat_id')} with {e}")
    return 


async def dashboard_data(username, image_table, chat_table, address_table):

    image_q = image_table\
            .select()\
            .where(image_table.username==username)\


    chat_q = chat_table\
            .select()\
            .where(chat_table.username==username)\


    address_q = address_table\
            .select()\
            .where(address_table.username==username)\

    return {"images": image_q.count(), "chats": chat_q.count(), "addresses": address_q.count()}

@aiomisc.threaded
def filter_images(tbl_object, username, start_date, end_date, skip, limit):
    logger.error(f"Name of the tanble is {tbl_object} --- {username}")

    if start_date and end_date:

        query = tbl_object\
                .select()\
                .where((
                        tbl_object.creation_timestamp> start_date) &\
                        (tbl_object.creation_timestamp < end_date) &\
                        (tbl_object.chat_image==False) &\
                        (tbl_object.username==username))\
                .order_by(-tbl_object.creation_timestamp)
                
        

    elif start_date and not end_date:
        query = tbl_object\
                        .select()\
                        .where((tbl_object.creation_timestamp> start_date)&\
                                (tbl_object.chat_image==False) &\
                             (tbl_object.username==username))\
                        .order_by(-tbl_object.creation_timestamp)
                        


    elif end_date and not start_date:
        query = tbl_object\
                        .select()\
                        .where((tbl_object.creation_timestamp < end_date)&\
                            (tbl_object.chat_image==False) &\
                            (tbl_object.username==username))\
                        .order_by(-tbl_object.creation_timestamp)
        


    else: # not  start_date and  not end_date

        query = tbl_object\
                .select()\
                .where(tbl_object.username==username, tbl_object.chat_image==False)\
                .order_by(-tbl_object.creation_timestamp)

    
    return query.offset(skip).limit(limit).dicts(), query.count()
    

@aiomisc.threaded
def filter_chats(tbl_object, username, start_date, end_date, skip, limit, search_text):
    logger.error(f"Name of the table is {tbl_object} --- {username}")

    if start_date and end_date:
        if search_text:
            query = tbl_object\
                                .select()\
                                .where((tbl_object.timestamp> start_date) &(tbl_object.timestamp < end_date)\
                                     & (tbl_object.username==username) &(tbl_object.message_content**f'%{search_text}%'))\
                                .order_by(-tbl_object.timestamp)

        else:
            query = tbl_object\
                    .select()\
                    .where((tbl_object.timestamp> start_date) &(tbl_object.timestamp < end_date) & (tbl_object.username==username))\
                    .order_by(-tbl_object.timestamp)
                
        

    elif start_date and not end_date:
        if search_text:
            query = tbl_object\
                        .select()\
                        .where((tbl_object.timestamp> start_date) \
                            & (tbl_object.username==username)&\
                                (tbl_object.message_content**f'%{search_text}%'))\
                        .order_by(-tbl_object.timestamp)

        else:
            query = tbl_object\
                            .select()\
                            .where((tbl_object.timestamp> start_date)& (tbl_object.username==username)&(tbl_object.message_content**f'%{search_text}%'))\
                            .order_by(-tbl_object.timestamp)
                        


    elif end_date and not start_date:
        if search_text:
            query = tbl_object\
                        .select()\
                        .where((tbl_object.timestamp < end_date) & (tbl_object.username==username)&(tbl_object.message_content**f'%{search_text}%'))\
                        .order_by(-tbl_object.timestamp)

        else:
            query = tbl_object\
                            .select()\
                            .where((tbl_object.timestamp < end_date)&((tbl_object.username==username)))\
                            .order_by(-tbl_object.timestamp)
        


    else: # not  start_date and  not end_date
        if search_text:
            query = tbl_object\
                            .select()\
                            .where(
                                tbl_object.message_content**f'%{search_text}%', tbl_object.username==username)\
                            .order_by(-tbl_object.timestamp)

        else:

            query = tbl_object\
                    .select()\
                    .where(tbl_object.username==username)\
                    .order_by(-tbl_object.timestamp)

    
    return query.offset(skip).limit(limit).dicts(), query.count()