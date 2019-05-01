

import plyvel
import json
    
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def instagram_batch_insert(posts):

    db = plyvel.DB("./database", create_if_missing=True)
    with db.write_batch() as wb:
        for post in posts: 
            if isinstance(post["image_id"], str):
                key = b'instagram_' + post["image_id"].encode()  
                value = json.dumps(post).encode()



            wb.put(key, value)

    db.close()
    return 

def create_db_instance(db_path):
    return plyvel.DB(db_path, create_if_missing=True)

def close_db_instance(db):
    db.close()
    logger.info("DB instance closed")
    return 


def insert_key(key, value, db_instance):
    logger.info(f"Inserting Key {key}")
    if isinstance(key, str):
        key = key.encode()
    

    if isinstance(value, str):
        value = value.encode()
    else:
        value = json.dumps(value).encode()
    

    try:
        db_instance.put(key, value)
    except Exception as e:
        logger.error(e)
    if not db_instance:
        db_instance.close()
    logger.info(f"Inserting Key Completed {key}")

    return 

def get_key(key, db_instance):
    logger.info(f"Get Key {key}")

    if isinstance(key, str):
        key = key.encode()

    #db = plyvel.DB("./database", create_if_missing=True)
    value = db_instance.get(key)
    if not value:
        return None


    try:
        
        return json.loads(value)  

    except json.JSONDecodeError:
        return value.decode()

    return 


def delete_key(key, db_instance):
    logger.info(f"Delete Key {key}")

    if isinstance(key, str):
        key = key.encode()

    value = db_instance.get(key)
    if not value:
        logger.error(f"Key is not present {key}")
        return None

    db_instance.delete(key)
    db_instance.close()

    return 