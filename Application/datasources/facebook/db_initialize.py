


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
        account_id = peewee.TextField(null=False)

    class Images(BaseModel):
        title = peewee.TextField()
        account_id = peewee.TextField(index=True, null=False)
        uri = peewee.TextField(index=True, unique=True, null=False)
        creation_timestamp = peewee.DateTimeField()
        media_metadata = peewee.BlobField()
        comments =  peewee.BlobField(null=True)

    class YourPosts(BaseModel):
        account_id = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        data = peewee.BlobField(null=True)
        attachments = peewee.BlobField(null=True)
        title = peewee.TextField(null=True)

    class OtherPosts(BaseModel):
        account_id = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField(index=True)
        data = peewee.BlobField(null=True)
        attachments = peewee.BlobField(null=True)
        title = peewee.TextField(null=True)

    class ContentDDD(FTSModel):
        content = peewee.TextField()
        account_id = peewee.TextField()
        content_hash = peewee.TextField()
        
        class Meta:
            database = db


    db.create_tables([
            Creds, 
            Images,
            OtherPosts,
            ContentDDD
        ])

    #db.drop_tables([FBImages])



    return Creds, Images, OtherPosts, ContentDDD

