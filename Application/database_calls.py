

import plyvel
import json
from kivy.logger import Logger
    


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

def create_db_instance():
    return plyvel.DB("./database", create_if_missing=True)

def close_db_instance(db):
    db.close()
    Logger.info("DB instance closed")
    return 


def insert(key, value, db_instance=None):
    Logger.info(f"Inserting Key {key}")
    if isinstance(key, str):
        key = key.encode()
    

    if isinstance(value, str):
        value = value.encode()
    else:
        value = json.dumps(value).encode()
    

    if not db_instance:
        db_instance = plyvel.DB("./database", create_if_missing=True)
    try:
        db_instance.put(key, value)
    except Exception as e:
        Logger.error(e)
    if not db_instance:
        db_instance.close()
    Logger.info(f"Inserting Key Completed {key}")

    return 

def get(key):
    Logger.info(f"Get Key {key}")

    if isinstance(key, str):
        key = key.encode()

    db = plyvel.DB("./database", create_if_missing=True)
    value = db.get(key)
    if not value:
        return None

    db.close()

    try:
        
        return json.loads(value)  

    except json.JSONDecodeError:
        return value.decode()

    return 


def delete(key):
    Logger.info(f"Delete Key {key}")

    if isinstance(key, str):
        key = key.encode()

    db = plyvel.DB("./database", create_if_missing=True)
    value = db.get(key)
    if not value:
        Logger.error(f"Key is not present {key}")
        return None

    db.delete(key)
    db.close()

    return 