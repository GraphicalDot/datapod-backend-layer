import aiomisc
#@retry(stop=stop_after_attempt(2))
import json
import datetime
from peewee import IntegrityError, OperationalError
from errors_module.errors import APIBadRequest, DuplicateEntryError
from loguru import logger

@aiomisc.threaded
def update_datasources_status(status_table, datasource_name, username, status):
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
def update_stats(stats_table, datasource_name, username, data_items, size, sync_frequency, sync_type, next_sync):
    """

    """
    try:
        stats_table.insert(
                source = datasource_name,
                username = username,
                data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).execute()
                                    
    except IntegrityError as e:
        logger.error(f"Couldnt insert stats for  {datasource_name} because of {e} so updating it")

        stats_table.update(
                            data_items = data_items,
                disk_space_used = size,
                sync_frequency = sync_frequency,
                sync_type = sync_type,
                next_sync = next_sync).\
        where(stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 




@aiomisc.threaded
def get_datasources_status(status_table):
    return status_table.select().dicts()
                                    

#@retry(stop=stop_after_attempt(2))
@aiomisc.threaded
def store_email(**data):
    """
    purchases: a list of purchases dict
    """
    email_table = data["tbl_object"]
    try:
        email_table.insert(email_id=data["email_id"], from_addr=data["from_addr"], 
                        to_addr=data["to_addr"], 
                        subject=data["subject"],
                        username = data["username"],
                        checksum=data["checksum"],
                        content=data["content"],
                        email_id_raw= data["email_id_raw"],
                        message_type = data["message_type"],
                        attachments = data["attachments"],
                       date=data["date"], path=data["path"]).execute()

        #logger.success(f"Success on insert email_id --{data['email_id']}-- path --{data['path']}--")
    except IntegrityError:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        raise DuplicateEntryError(data['email_id'], "Email")

    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email data insertion failed {data['email_id']} with {e}")
 
    return 

@aiomisc.threaded
def store_email_content(**data):
    """
    purchases: a list of purchases dict
    """
    index_email_content_table = data["tbl_object"]

    try:
        index_email_content_table.insert(email_id=data["email_id"], 
                        content=data["content"],
                           username = data["username"],
                        checksum=data["checksum"],
                        content_hash=data["content_hash"]).execute()

        #logger.success(f"Success on insert indexed content for  email_id --{data['email_id']}-- ")


    except IntegrityError as e:
        logger.error(f"Error on insert indexed content for  email_id --{data['email_id']}-- with error {e}")
    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email content insertion failed {data['email_id']} with {e}")
    return



#@retry(stop=stop_after_attempt(2))
@aiomisc.threaded
def store_email_attachment(**data):
    """
    purchases: a list of purchases dict
    """
    email_attachment_table = data["tbl_object"]
    try:
        email_attachment_table.insert(email_id=data["email_id"], 
                        path=data["path"], 
                           username = data["username"],
                        checksum=data["checksum"],
                        attachment_name=data["attachment_name"], 
                        message_type= data["message_type"],
                       date=data["date"]).execute()

        # logger.success(f"Success on insert attachement for  email_id --{data['email_id']}--  \
        #                             path --{data['path']}-- and attachement name {data['attachment_name']}")

    except IntegrityError as e:
        logger.error(f"Error on insert attachement for  email_id --{data['email_id']}--  \
                                    path --{data['path']}-- and attachement name {data['attachment_name']}\
                                    with error {e}")
    except Exception as e:
        #raise DuplicateEntryError(data['email_id'], "Email")
        #use with tenacity
        logger.error(f"Email sttachment insertion failed {data['email_id']} with {e}")
    return 



@aiomisc.threaded
def get_email_attachment(tbl_object, message_type, start_date, end_date, skip, limit):
    """
    purchases: a list of purchases dict
    """
    # email_attachment_table = tbl_object
    # return email_attachment_table\
    #             .select()\
    #             .order_by(-email_attachment_table.date)\
    #             .paginate(page, number)\
    #             .dicts()

    if start_date and end_date:
        logger.info("Start date and  end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date) &(tbl_object.date < end_date))
                
        

    elif start_date and not end_date:
                        
        logger.info("Start date and but not end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date))
                

    elif end_date and not start_date:
        logger.info("not Start date and but end date")
        
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date < end_date))
                


    else: # not  start_date and  not end_date
        logger.info("Start date and end date is not present")
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where(tbl_object.message_type== message_type)
                

    return  query.offset(skip).limit(limit).dicts(), query.count()



@aiomisc.threaded
def get_emails(tbl_object, message_type, start_date, end_date, skip, limit):
    """
    purchases: a list of purchases dict
    """


    # return email_attachment_table\
    #             .select()\
    #             .order_by(-email_attachment_table.date)\
    #             .where(email_attachment_table.message_type== message_type)\
    #             .paginate(page, number)\
    #             .dicts()



    if start_date and end_date:
        logger.info("Start date and  end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date) &(tbl_object.date < end_date))
                
        

    elif start_date and not end_date:
                        
        logger.info("Start date and but not end date")

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date> start_date))
                

    elif end_date and not start_date:
        logger.info("not Start date and but end date")
        
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where((tbl_object.message_type== message_type)& (tbl_object.date < end_date))
                


    else: # not  start_date and  not end_date
        logger.info("Start date and end date is not present")
        query = tbl_object\
                .select()\
                .order_by(-tbl_object.date)\
                .where(tbl_object.message_type== message_type)
                

    return  query.offset(skip).limit(limit).dicts(), query.count()

@aiomisc.threaded
def match_text(tbl_object, indexed_obj, matching_string, message_type, start_date, end_date, skip, limit):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    # query = (tbl_object
    #             .select()
    #             .join(index_email_obj, on=(email_tbl_object.email_id == index_email_obj.email_id))
    #             .where(index_email_obj.match(matching_string))
    #             .dicts())
    # return list(query)

    

    if start_date and end_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id))\
                .where(indexed_obj.match(matching_string) & (tbl_object.date> start_date) &(tbl_object.date < end_date) &(tbl_object.message_type== message_type))\
                .order_by(-tbl_object.date)

                
        

    elif start_date and not end_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id))\
                .where((indexed_obj.match(matching_string)) & (tbl_object.date> start_date) &(tbl_object.message_type== message_type))\
                .order_by(-tbl_object.date)

        


    elif end_date and not start_date:
        query = tbl_object\
                .select()\
                .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id))\
                .where((indexed_obj.match(matching_string)) &(tbl_object.date < end_date) & (tbl_object.message_type== message_type))\
                .order_by(-tbl_object.date)



    else: # not  start_date and  not end_date
        query = tbl_object\
                    .select()\
                    .join(indexed_obj, on=(tbl_object.email_id == indexed_obj.email_id) &(tbl_object.message_type== message_type))\
                    .where(indexed_obj.match(matching_string))\


    return  query.offset(skip).limit(limit).dicts(), query.count()


@aiomisc.threaded
def store_images(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    try:
        geo_data = json.dumps(data['geo_data'])
        table.insert( 
                        creation_time=data["creation_time"], 
                        modification_time=data["modification_time"], 
                           username = data["username"],
                        checksum=data["checksum"],
                        photo_taken_time=data["photo_taken_time"],
                        description=data["description"],
                        url=data["url"], 
                        title=data["title"], 
                        geo_data=data["geo_data"], 
                        image_path=data["image_path"]).execute()

        logger.success(f"IMAGES: success on insert {data['username']} image {data['image_path']}")

    except OperationalError  as e:
        logger.error(f"IMAGES: Couldnt save image data {data['username']}  because of {e}")

    except IntegrityError as e:
        logger.error(f"IMAGES: Duplicate image key exists {data['username']}  because of {e}")

    # except Exception as e:
    #     logger.error(f"IMAGES: {data['username']}  because of {e}")

    return 




@aiomisc.threaded
def filter_images(tbl_object, start_date, end_date, skip, limit):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    ##startDate must be greater then Enddate


    if start_date and end_date:

        query = tbl_object\
                .select()\
                .where((tbl_object.creation_time> start_date) &(tbl_object.creation_time < end_date))\
                .order_by(-tbl_object.creation_time)
                
        

    elif start_date and not end_date:
        query = tbl_object\
                        .select()\
                        .where(tbl_object.creation_time> start_date)\
                        .order_by(-tbl_object.creation_time)\
                        


    elif end_date and not start_date:
        query = tbl_object\
                        .select()\
                        .where(tbl_object.creation_time < end_date)\
                        .order_by(-tbl_object.creation_time)\
        


    else: # not  start_date and  not end_date

        query = tbl_object\
                .select()\
                .order_by(-tbl_object.creation_time)\


    return  query.offset(skip).limit(limit).dicts(), query.count()


@aiomisc.threaded
def store_purchases(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    try:
        products = json.dumps(data["products"])
        table.insert(merchant_name=data["merchant_name"],  
                                    products=data["products"], 
                                    username = data["username"],
                                    checksum=data["checksum"],
                                    time=data["time"]).execute()
        logger.info(f"On insert the purchase for  {data['merchant_name']}")
    except OperationalError  as e:
        logger.error(f"PURCHASES: Couldnt save purchase data {data['merchant_name']}  because of {e}")

    except IntegrityError as e:
        logger.error(f"PURCHASES: Duplicate key exists {data['merchant_name']}  because of {e}")
    
    return 


def store_reservations(**data):
    """
    purchases: a list of purchases dict
    """
    table = data["tbl_object"]

    try:
        table.insert(merchant_name=data["merchant_name"],  
                            src= data["src"],
                            dest=data["dest"],
                            username = data["username"],
                            checksum=data["checksum"],
                            time=data["time"]).execute()

        logger.info(f"On insert the reservations for  {data['merchant_name']}")
    except OperationalError  as e:
        logger.error(f"RESERVATIONS: Couldnt save reservations data {data['merchant_name']}  because of {e}")

    except IntegrityError as e:
        logger.error(f"RESERVATIONS: Duplicate key exists {data['merchant_name']}  because of {e}")

    return 
