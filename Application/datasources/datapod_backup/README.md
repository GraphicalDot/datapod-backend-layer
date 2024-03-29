


```
In [81]: r = requests.get("http://localhost:8000/datasources/users/generate_mnemonic")                                                                                                                                                                                                   

In [82]: r.json()                                                                                                                                                                                                                                                                        
Out[82]: 
{'error': True,
 'success': False,
 'message': None,
 'data': {'mnemonic_phrase_0': 'friend',
  'mnemonic_phrase_1': 'hour',
  'mnemonic_phrase_2': 'piano',
  'mnemonic_phrase_3': 'captain',
  'mnemonic_phrase_4': 'advice',
  'mnemonic_phrase_5': 'buddy',
  'mnemonic_phrase_6': 'skull',
  'mnemonic_phrase_7': 'omit',
  'mnemonic_phrase_8': 'athlete',
  'mnemonic_phrase_9': 'praise',
  'mnemonic_phrase_10': 'dumb',
  'mnemonic_phrase_11': 'humble',
  'mnemonic_phrase_12': 'feel',
  'mnemonic_phrase_13': 'rely',
  'mnemonic_phrase_14': 'cat',
  'mnemonic_phrase_15': 'prize',
  'mnemonic_phrase_16': 'range',
  'mnemonic_phrase_17': 'garage',
  'mnemonic_phrase_18': 'aim',
  'mnemonic_phrase_19': 'average',
  'mnemonic_phrase_20': 'mansion',
  'mnemonic_phrase_21': 'vapor',
  'mnemonic_phrase_22': 'verify',
  'mnemonic_phrase_23': 'evidence'}}
```



```
mnemonic = ['friend', 'hour', 'piano', 'captain', 'advice', 'buddy', 'skull', 'omit', 'athlete', 'praise', 'dumb', 'humble', 'feel', 'rely', 'cat', 'prize', 'range', 'garage', 'aim', 'average', 'mansion', 'vapor', 'verify', 'evidence']

In [144]: r = requests.post("http://localhost:8000/datasources/backup/store_mnemonic", data=json.dumps({"mnemonic": mnemonic}))                                                                                                                                                          

In [145]: r.json()                                                                                                                                                                                                                                                                       
Out[145]: 
{'message': 'User is not logged in',
 'error': True,
 'success': False,
 'Data': None}

In [146]: r = requests.post("http://localhost:8000/datasources/backup/store_mnemonic", data=json.dumps({"mnemonic": mnemonic}))                                                                                                                                                          

In [147]: r.json()                                                                                                                                                                                                                                                                       
Out[147]: 
{'message': 'The Mnemonic is already present for this user',
 'error': True,
 'success': False,
 'Data': None}

In [148]: r = requests.post("http://localhost:8000/datasources/backup/store_mnemonic", data=json.dumps({"mnemonic": mnemonic}))                                                                                                                                                          

In [149]: r.json()                                                                                                                                                                                                                                                                       
Out[149]: 
{'error': True,
 'success': False,
 'message': 'Mnemonic has been saved and updated',
 'data': None}
```

API to be used when user has reinstalled datapod since he/she already has menmonic intialized somewhere in the past ,
this mnemonic has to be checked against the hash of the Mnemonic  

```
r = requests.post("http://localhost:8000/datasources/backup/check_mnemonic", data=json.dumps({"mnemonic": mnemonic}))                                                                                                                                                          
r.json()                                                                                                                                                                                                                                                                       
Out[154]: 
{'message': 'The mnemonic is already present',
 'error': True,
 'success': False,
 'Data': None}

```

```
To start a fresh Backup 

r = requests.get("http://localhost:8000/datasources/backup/start_fresh_backup")  
```

List of all backups which have been made 

```
In [22]: r = requests.get("http://localhost:8000/datasources/backup/backup_list")                                                                                                                                                                                                        

In [23]: r.json()                                                                                                                                                                                                                                                                        
Out[23]: 
{'error': False,
 'success': True,
 'data': [{'archive_name': 'December-25-2019_13-59-08',
   'last_modified': '25-12-2019',
   'size': '945.7 kB'},
  {'archive_name': 'December-25-2019_12-55-17',
   'last_modified': '25-12-2019',
   'size': '12.6 GB'}],
 'message': None}


```
