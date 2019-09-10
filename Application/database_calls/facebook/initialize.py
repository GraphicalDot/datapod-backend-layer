


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase


def facebook_initialize(db):

    class BaseModel(peewee.Model):
        class Meta:
            database = db


    # class Owner(BaseModel):
    #     login = peewee.TextField()
    #     id = peewee.IntegerField()
    #     node_id = peewee.TextField()
    #     avatar_url = peewee.TextField()
    #     gravatar_id = peewee.TextField(null=True)
    #     url = peewee.TextField()
    #     html_url = peewee.TextField()
    #     type = peewee.TextField()
    #     site_admin = peewee.BooleanField()

    class FacebookCreds(BaseModel):
        username = peewee.TextField(unique=True, null=False)
        password = peewee.TextField(null=False)
        

    class FBImages(BaseModel):
        title = peewee.TextField()
        uri = peewee.TextField(index=True, null=False)
        creation_timestamp = peewee.DateTimeField()
        media_metadata = peewee.BlobField()
        comments =  peewee.BlobField(null=True)

    db.create_tables([
            FacebookCreds, 
            FBImages
        ])

    #db.drop_tables([FBImages])



    return FacebookCreds, FBImages

