


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase


def initialize(db):

    class BaseModel(peewee.Model):
        class Meta:
            database = db




    class FacebookCreds(BaseModel):
        username = peewee.TextField(unique=True, null=False)
        password = peewee.TextField(null=False)
        identifier = peewee.TextField(null=False)


    class FacebookStatus(BaseModel):
        source = peewee.TextField(index=True)
        username = peewee.TextField(null=True, unique=True)
        status = peewee.TextField(null=True)
        last_updated =  peewee.DateTimeField(default=datetime.datetime.now)


    class FacebookStats(BaseModel):
        source = peewee.TextField(index=True)
        username = peewee.TextField(null=True, unique=True)
        data_items = peewee.IntegerField(null=True)
        disk_space_used = peewee.TextField(null=True)
        sync_frequency = peewee.TextField(null=True)
        sync_type = peewee.TextField(null=True)
        last_sync = peewee.DateTimeField(default=datetime.datetime.now)
        next_sync = peewee.DateTimeField(default=datetime.datetime.now)

    class FacebookArchives(BaseModel):
        path = peewee.TextField(null=False)
        username = peewee.TextField(unique=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class FacebookImages(BaseModel):
        title = peewee.TextField()
        username = peewee.TextField(index=True, null=False)
        uri = peewee.TextField(index=True, unique=True, null=False)
        creation_timestamp = peewee.DateTimeField()
        media_metadata = peewee.BlobField()
        comments =  peewee.BlobField(null=True)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class FacebookYourPosts(BaseModel):
        username = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        data = peewee.BlobField(null=True)
        attachments = peewee.BlobField(null=True)
        title = peewee.TextField(null=True)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class FacebookOtherPosts(BaseModel):
        username = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        data = peewee.BlobField(null=True)
        attachments = peewee.BlobField(null=True)
        title = peewee.TextField(null=True)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

    class FacebookContent(FTSModel):
        username = peewee.TextField()
        content = peewee.TextField()
        account_id = peewee.TextField()
        content_hash = peewee.TextField()
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()
        
        class Meta:
            database = db


    db.create_tables([
            FacebookCreds,
            FacebookArchives, 
            FacebookImages,
            FacebookYourPosts,
            FacebookOtherPosts,
            FacebookContent,
            FacebookStatus, 
            FacebookStats
        ])

    db.drop_tables([  
            # FacebookCreds,
            # FacebookArchives, 
            # FacebookImages,
            # FacebookYourPosts,
            # FacebookOtherPosts,
            # FacebookContent,
            # FacebookStatus

        ])



    return FacebookCreds, FacebookArchives, FacebookImages, \
            FacebookYourPosts, FacebookOtherPosts, FacebookContent,\
            FacebookStatus, FacebookStats

