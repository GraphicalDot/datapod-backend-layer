

import plyvel
import json
import imghdr
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


class StoreInChunks(object):
    def __init__(self, main_key,  data, db_instance, sub_key=None):
        self.main_key = main_key
        self.data = data
        self.db_instance = db_instance
        self.sub_key  = sub_key
        if not self.sub_key:
            extension = imghdr.what(data["path"])
            if extension == "png":
                self.sub_key = "gmail_images_png"
            else:
                self.sub_key = "gmail_images_rest"

        ##turn for sub_sub_key i.e gmail_images_1, gmail_images_2 etc
        self.old_sub_sub_key = None
        self.new_sub_sub_key = None

        ##the last index present in the arr for sub_key, which 
        ##prvovides the basis for self.sub_sub_key
        self.last_index = None


    def if_main_exists(self):
        """
        Check if main_db exists or not
        main_data corresponds to the main data for the key, which 
        hold info about data for child keys 
        """
        self.main_data = get_key(self.main_key, self.db_instance)
        if not self.main_data:
            print (f"Key corresponding to the main key doesnt exists key = {self.main_key}")
            self.main_data = {}
            
    def update_sub_key(self, data):
        self.main_data.update({self.sub_key: data})
        insert_key(self.main_key, self.main_data, self.db_instance)
        return 

    def if_sub_exists(self):
        """
        Check if data corresponding to the subkey exists or not, 
        if sub_key dosent exists then sub_sub_key = self.sub_key_1
        """
        if not self.main_data.get(self.sub_key):
            ##implies this is the first time this sub_key has been 
            ##accessed
            print (f"Key corresponding to the sub key doesnt exists sub_key = {self.sub_key}")
            
            self.old_sub_sub_key =  self.sub_key + "_"+ "1"
            print (f"Key corresponding to the old_sub_sub key doesnt exists  = {self.old_sub_sub_key}")

            self.update_sub_key([1])

            #self.main_data.update({sub_key: [1]})
            #insert_key("gmail", gmail, db_instance)
            self.last_index = 0

        else:
            ##if the sub key already exists, ge tthe last idex and 
            #the new key present in the database
            print (f"Key corresponding to the sub key  exists  = {self.sub_key}")

            self.last_indexes = self.main_data.get(self.sub_key)
            print (f"Indexes stored against the sub_key {self.sub_key} and indexes are {self.last_indexes}")
            self.last_index = self.last_indexes[-1]
            self.old_sub_sub_key = self.sub_key + "_" +  str(self.last_index)

            print (f"Key corresponding to the old_sub_sub key  exists  = {self.old_sub_sub_key}")


    def sub_sub_key_data(self):
        return  get_key(self.old_sub_sub_key, self.db_instance)


    def insert(self):
        ##cehck if value corresponding to the self.main_key eixsts or not
        self.if_main_exists()

        ##check if value cirresponding to the sub_key exists, if not 
        ##update main_key with sub_key data and sub_sub_key will be made available
        self.if_sub_exists()

        ##get sub_sub_data from the self.sub_sub_key
        sub_sub_data = self.sub_sub_key_data()
        print (f"Data corresponding to the old_sub_sub key={self.old_sub_sub_key} is {sub_sub_data}")

        if not sub_sub_data:
            sub_sub_data = [self.data]
            self.new_sub_sub_key = self.old_sub_sub_key
            print (f"Data corresponding to the sub_sub key={self.new_sub_sub_key} doesnt exists")


        elif len(sub_sub_data) >= 20:
            sub_sub_data = [self.data]
            self.last_index+=1
            self.new_sub_sub_key = self.sub_key + "_" +  str(self.last_index)

            ##appending last indexes with new index after incrementing
            self.last_indexes.append(self.last_index)
            self.main_data.update({self.sub_key: self.last_indexes})
            insert_key(self.main_key, self.main_data, self.db_instance)
            print (f"Data corresponding to the sub_sub key={self.new_sub_sub_key} doesnt exists")


        else:
            self.new_sub_sub_key = self.old_sub_sub_key
            print(f"Length of sub_sub_data {len(sub_sub_data)} must be appended to existsking \
                        sub_sub_key {self.new_sub_sub_key}")

            sub_sub_data.append(self.data)
    
        insert_key(self.new_sub_sub_key, sub_sub_data, self.db_instance)
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