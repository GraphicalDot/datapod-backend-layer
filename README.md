
To build backend image for datapod from the updated code 
```
 sudo docker build -t datapod_ubuntu_1604 .
 ##this will not run  the container 
 sudo docker create -ti --name datapod_container  datapod_ubuntu_1604 bash
	
 ##this will run the container
 sudo docker run  -p 8000:8000 -it --name datapod_ubuntu_1604_container datapod_ubuntu_1604
 sudo docker cp datapod_ubuntu_1604_container:/releases/Datapod_ubuntu <Destination to copy>
 ```

To be used with UPX
Download UPX binary from their official repository and copy it to /usr/local/share

```
pyinstaller Datapod_ubuntu.spec --upx-dir=/usr/local/share   --distpath releases/
```

r = requests.get("http://localhost:8000/datasources/google/emails/filter", params={"username": "dummy.houzier.saurav@gmail.com", "message_type": "Inbox", "attachments": True, "match_string": "ube"})




common functions which must be defined by a module in their db_calls. 


```

@aiomisc.threaded
def update_status(table, datasource_name, username, status, path=None, original_path=None):
    try:
        table.insert(source=datasource_name,  
                                    username=username,
                                    status=status,
                                    path = path,
                                    original_path=original_path
                                    ).execute()
                                    

    except IntegrityError as e:
        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        logger.error(f"Couldnt insert {datasource_name} because of {e} so updating it")

        if path and original_path:
            table.update(
                status=status, 
                path = path,
                original_path=original_path).\
            where(table.username==username).\
            execute()
        elif original_path:
            table.update(
                            status=status, 
                            original_path=original_path).\
                        where(table.username==username).\
                        execute()

        elif path:
            table.update(
                            status=status, 
                            path=path).\
                        where(table.username==username).\
                        execute()
        else:
            table.update(
                            status=status).\
                        where(table.username==username).\
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
                disk_space_used = size).\
        where(stats_table.username==username).\
        execute()

    except Exception as e:
        logger.error(f"Couldnt {datasource_name} updated because of {e}")
    return 





@aiomisc.threaded
def get_status(table, username=None):
    logger.info(f"This is the username {username}")
    if not username:
        return table.select().dicts()
    return table.select().where(table.username==username).dicts()
                                

@aiomisc.threaded
def get_stats(stats_table):
    return stats_table.select().dicts()
        


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

```


Every module should also defined Route class in their settings.py file which must expose GET, POST, DELETE requests 
Expose all the tables
Expose two must functions stats and status


```

class Routes:
    def __init__(self, db_path):
        pragmas = [
            ('journal_mode', 'wal2'),
            ('cache_size', -1024*64)]
        
        self.db_path = os.path.join(db_path, DATASOURCE_NAME, f"{DATASOURCE_NAME}.db")        
        self.db_object = SqliteExtDatabase(self.db_path, pragmas=pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)


        creds_table, status_table, stats_table, email_table,\
             email_attachment_table, email_content_table,\
             image_table, purchase_table, reservation_table, \
                 archives_table, location_table, location_approximate_table = initialize(self.db_object)                  
        self.datasource_name = DATASOURCE_NAME

        self.config  = { 
            "tables": { 
                "creds_table": creds_table,
                "image_table" : image_table,
                "email_table": email_table,
                "email_attachment_table": email_attachment_table,
                "email_content_table": email_content_table,
                "purchase_table": purchase_table,
                "archives_table": archives_table,
                "reservation_table": reservation_table,
                "location_table": location_table,
                "location_approximate_table": location_approximate_table,
                "stats_table": stats_table, 
                "status_table": status_table},
            "utils":{
                "stats": stats, 
                "status": status
            }
        }
        
        self.routes = {"GET": [("emails/filter", emails_filter), ("images/filter", image_filter), ("locations/filter", locations_filter), 
                    ("delete_zip", delete_original_path),
                    ("purchases/filter", purchases_filter), ("reservations/filter", reservations_filter), ("attachments/filter", attachment_filter)], 
                    "POST": [("parse", parse)] } 
```


Every module should define DATASOURCE_NAME in variables.py file

```


DATASOURCE_NAME = "Facebook"
DEFAULT_SYNC_TYPE = "manual"
DEFAULT_SYNC_FREQUENCY = "weekly"
```



```
r = requests.post("http://localhost:8000/datasources/users/forgot_password", data=json.dumps({"username": "graphicaldote"}))                                                                                                                        r.json()                                                                                                                                                                                                                                            
    {'message': 'Username doesnt exists',
    'error': True,
    'success': False,
    'Data': None}

r = requests.post("http://localhost:8000/datasources/users/forgot_password", data=json.dumps({"username": "graphicaldot"}))                                                                                                                         r.json()                                                                                                                                                                                                                                            
        {'error': False,
        'success': True,
        'message': 'Please check your Registered email id for validation code',
        'data': None}

r = requests.post("http://localhost:8000/datasources/users/confirm_forgot_password", data=json.dumps({"username": "graphicaldot"}))                                                                                                                                             
r = requests.post("http://localhost:8000/datasources/users/confirm_forgot_password", data=json.dumps({"username": "graphicaldot", "newpassword": "GHDYYDEddd98@#"}))                                                                                                            
        {'message': 'validation_code is required',
        'error': True,
        'success': False,
        'Data': None}

In [26]: r = requests.post("http://localhost:8000/datasources/users/confirm_forgot_password", data=json.dumps({"username": "graphicaldot", "password": "BIGwedding98@#", "code": "32324444" }))                                                                                          

In [27]: r.json()                                                                                                                                                                                                                                                                        
Out[27]: 
    {'message': 'Invalid Verification code',
    'error': True,
    'success': False,
    'Data': None}

In [28]: r = requests.post("http://localhost:8000/datasources/users/confirm_forgot_password", data=json.dumps({"username": "graphicaldot", "password": "BIGwedding98@#", "code": "390747" }))                                                                                            

In [29]: r.json()                                                                                                                                                                                                                                                                        
Out[29]: 
    {'error': False,
    'success': True,
    'message': 'Password has been changed successfully',
    'data': None}
```