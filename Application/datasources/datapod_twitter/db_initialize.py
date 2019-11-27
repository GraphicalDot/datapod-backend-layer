


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase
"""
user_mentions is alos a list of dicts
'entities': {'hashtags': [{'text': 'AI', 'indices': ['31', '34']},
   {'text': 'machinelearning', 'indices': ['39', '55']}],
  'symbols': [],
  'user_mentions': [],
  'urls': [{'url': 'https://t.co/x1c6JxZ3CB',
    'expanded_url': 'http://www.forbes.com/sites/louiscolumbus/2018/02/18/roundup-of-machine-learning-forecasts-and-market-estimates-2018/',
    'display_url': 'forbes.com/sites/louiscol…',
    'indices': ['103', '126']}]
"""


def initialize(db):

    class BaseModel(peewee.Model):
        class Meta:
            database = db

    
    class Creds(BaseModel):
        username = peewee.TextField(unique=True, null=False)
        password = peewee.TextField(null=False)



    class Status(BaseModel):
        source = peewee.TextField(index=True)
        username = peewee.TextField(null=True, unique=True)
        status = peewee.TextField(null=True)
        last_updated =  peewee.DateTimeField(default=datetime.datetime.now)
        path = peewee.TextField(null=True)
        original_path = peewee.TextField(null=True)
        checksum = peewee.TextField(index=True, null=True)
        percentage = peewee.IntegerField(null=True)


    class Stats(BaseModel):
        source = peewee.TextField(index=True)
        username = peewee.TextField(null=True, unique=True)
        data_items = peewee.IntegerField(null=True)
        disk_space_used = peewee.TextField(null=True)
        sync_frequency = peewee.TextField(null=True)
        sync_type = peewee.TextField(null=True)
        last_sync = peewee.DateTimeField(default=datetime.datetime.now)
        next_sync = peewee.DateTimeField(default=datetime.datetime.now)


    class Archives(BaseModel):
        path = peewee.TextField(null=False)
        username = peewee.TextField(unique=False, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)    

    class AccountData(BaseModel):
        username = peewee.TextField(unique=False, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)    

        phone_number=peewee.TextField(null=True)
        email = peewee.TextField(null=True)
        created_via = peewee.TextField(null=True)
        username = peewee.TextField(null=True)
        account_id = peewee.TextField(index=True, unique=True, null=True)
        created_at=peewee.DateTimeField(null=True)
        account_display_name = peewee.TextField(null=True)


        follower_count = peewee.IntegerField(null=True) 
        following_count = peewee.IntegerField(null=True)
        list_created = peewee.IntegerField(null=True)
        list_subscribed= peewee.IntegerField(null=True)
        list_member = peewee.IntegerField(null=True)
        likes = peewee.IntegerField(null=True)
        contacts = peewee.IntegerField(null=True)
        tweets = peewee.IntegerField(null=True)
        common_hashtags = peewee.BlobField(null=True) 
        common_user_mentions = peewee.BlobField(null=True)


    class TweetObject(BaseModel):
        username = peewee.TextField(unique=False, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=False, null=False)    

        tweet_hash = peewee.TextField(index=True, unique=True,null=False)
        retweeted = peewee.BooleanField(null=True)
        source = peewee.TextField(null=True) #<a href="http://twitter.com" rel="nofollow">Twitter Web Client</a>',
        entities = peewee.BlobField(null=True)
        symbols = peewee.BlobField(null=True)
        display_text_range=peewee.BlobField(null=True)
        favorite_count= peewee.TextField(null=True)
        id_str=peewee.TextField(null=True)
        possibly_sensitive = peewee.BooleanField(null=True)
        truncated=peewee.BooleanField(null=True)
        retweet_count=peewee.TextField(null=True)
        hashtags=peewee.TextField(null=True)
        user_mentions = peewee.TextField(null=True)
    
        created_at=peewee.DateTimeField(index=True, null=True)
        favorited=peewee.BooleanField(null=True)
        full_text=peewee.TextField(null=False)
        lang=peewee.TextField(null=True)
        in_reply_to_screen_name=peewee.TextField(null=True)
        in_reply_to_user_id_str=peewee.TextField(null=True)
        
        # class Meta:
        #     indexes = ((('tweet_hash', 'nofull_textde_id'), True),)

    class IndexTweetContent(FTSModel):
        username = peewee.TextField(unique=False, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(null=False)    

        content = peewee.TextField()
        tweet_hash = peewee.TextField()
        class Meta:
            database = db


    db.create_tables([
            Creds,
            Status, 
            Stats, 
            Archives,
            AccountData,
            TweetObject, 
            IndexTweetContent
        ])

    #db.drop_tables([TweetObject, IndexTweetContent, TweetAccountData])
    #db.drop_tables([TweetAccountData])



    return  Creds, Status, Stats, Archives, AccountData, TweetObject, IndexTweetContent
