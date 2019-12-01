


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase


def initialize(db):

    class BaseModel(peewee.Model):
        class Meta:
            database = db




    class Creds(BaseModel):
        username = peewee.TextField(unique=True, null=False)
        password = peewee.TextField(null=False)
        identifier = peewee.TextField(null=False)


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
        username = peewee.TextField(unique=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class Images(BaseModel):
        title = peewee.TextField()
        username = peewee.TextField(index=True, null=False)
        uri = peewee.TextField(index=True, unique=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        media_metadata = peewee.BlobField(null=True)
        comments =  peewee.BlobField(null=True)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)
        chat_image = peewee.BooleanField(default=False)
        file_extension = peewee.TextField(null=True)

    class YourPosts(BaseModel):
        username = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        data = peewee.BlobField(null=True)
        attachments = peewee.BlobField(null=True)
        title = peewee.TextField(null=True)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class OtherPosts(BaseModel):
        username = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        data = peewee.BlobField(null=True)
        attachments = peewee.BlobField(null=True)
        title = peewee.TextField(null=True)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class Chats(BaseModel):
        username = peewee.TextField(index=True, null=False)
        checksum = peewee.TextField(index=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)

        participants = peewee.TextField(null=True)
        messages = peewee.TextField(null=True)
        message_content = peewee.TextField(null=True) 
        title = peewee.TextField( null=True)
        thread_type = peewee.TextField(null=True)
        timestamp = peewee.DateTimeField(index=True)
        chat_type = peewee.TextField(null=False)
        chat_id = peewee.TextField(index=True,null=False)
        chat_path = peewee.TextField(null=False)

    class Address(BaseModel):
        username = peewee.TextField(index=True, null=False)
        checksum = peewee.TextField(index=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)

        name = peewee.TextField(null=True)
        email = peewee.TextField(null=True)
        phone_number = peewee.TextField(null=True) 
        
        created_timestamp = peewee.DateTimeField()
        updated_timestamp = peewee.DateTimeField()

    class ChatContent(FTSModel):
        username = peewee.TextField()
        checksum = peewee.TextField()
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)

        content = peewee.TextField()
        content_hash = peewee.TextField()
        class Meta:
            database = db

    class FContent(FTSModel):
        username = peewee.TextField()
        content = peewee.TextField()
        account_id = peewee.TextField()
        content_hash = peewee.TextField()
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()
        
        class Meta:
            database = db


    db.create_tables([
            Creds,
            Archives, 
            Images,
            YourPosts,
            OtherPosts,
            FContent,
            Status, 
            Stats,
            Chats, 
            ChatContent, 
            Address
        ])

    db.drop_tables([  
            # Creds,
            # Archives, 
            # Images,
            # YourPosts,
            # OtherPosts,
            # Content,
            # Status

        ])



    return Creds, Archives, Images, YourPosts, OtherPosts, FContent, Status, Stats, Chats, ChatContent, Address

