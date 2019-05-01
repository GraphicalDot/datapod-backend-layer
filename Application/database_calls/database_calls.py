

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
    print("DB instance closed")
    return 


def insert_key(key, value, db_instance):
    print(f"Inserting Key {key}")
    if isinstance(key, str):
        key = key.encode()
    

    if isinstance(value, str):
        value = value.encode()
    else:
        value = json.dumps(value).encode()
    

    try:
        db_instance.put(key, value)
    except Exception as e:
        print(e)
    if not db_instance:
        db_instance.close()
    print(f"Inserting Key Completed {key}")

    return 

def get_key(key, db_instance):
    print(f"Get Key {key}")

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




def store_google_images(image_data, db_instance):
    """
    First lets create a key calles as google, and lets store different keys in it
    gmail: {"gmail_images_png": [1, 2, 3, ...], 
            gmail_images_rest": [1, 2, 3, ...],
            "gmail_pdf": [1, 2, 3, ...], 
            "gmail_extra": [1, 2, 3, ....]} 

    every index in each list represent 30 elements for example, 
    gmail_images has 1, 2, 3 elements then the leveldb must have 
    three databases gmail_images_1, email_images_2, ...
    """

    extension = image_data["path"].split(".")[-1]
    
    gmail = get_key("gmail", db_instance)
    print(f"Data for gmail key {gmail}")

    ##DEciding on the basis of image extension
    if extension == "png":
        sub_key = "gmail_images_png"
    else:
        sub_key = "gmail_images_rest"

    ##if the sub_key doesnt exists create one under gmail key and 
    ##corresponding to this sub_key, make a list with key 1 
    if not gmail:
        gmail = {}

    if not gmail.get(sub_key):
        key =  "%s_1"%sub_key
        gmail.update({sub_key: [1]})
        insert_key("gmail", gmail, db_instance)
        last_index = 0
        print(f"sub key doesnt exists {sub_key} and the db key will be {key}")

    else:
        ##if the sub key already exists, ge tthe last idex and 
        #the new key present in the database
        last_index = gmail.get(sub_key)[-1]
        key = "%s_%s"%(sub_key, last_index)
        print(f"sub key exists {sub_key} and the db key will be {key}")


    ## Get the key corresponding to the key
    google_images = get_key(key, db_instance)
    print (f"data for google_images is {google_images}")
    if not google_images or len(google_images) >=5:
        data = [image_data]
        last_index+=1
        key = "%s_%s"%(sub_key, last_index)
        print(f"New key is being created because of image arr length is more than 5 {key}")
    else:
        print(f"Length of google images {len(google_images)} must be appended to existsking key {key}")
        data = google_images.append(image_data)
        print (data)


    insert_key(key, data, db_instance)
    return

def delete_key(key, db_instance):
    print(f"Delete Key {key}")

    if isinstance(key, str):
        key = key.encode()

    value = db_instance.get(key)
    if not value:
        logger.error(f"Key is not present {key}")
        return None

    db_instance.delete(key)
    db_instance.close()

    return 