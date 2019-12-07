


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase


def initialize(db):

    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Credentials(BaseModel):
        ##blocfileds will be stored in bytes
        name = peewee.TextField(null=True)
        email = peewee.TextField(null=False)
        username = peewee.CharField(unique=True)
        mnemonic = peewee.TextField(null=True)
        id_token = peewee.BlobField(null= True)
        access_token = peewee.BlobField(null= True)
        password_hash = peewee.TextField(null=False)
        password = peewee.TextField(null=False)
        refresh_token = peewee.BlobField(null= True)
        salt = peewee.TextField(null= True)
        address = peewee.TextField(null=True)
        encryption_key = peewee.TextField(null=True)




    db.create_tables([
            Credentials
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



    return Credentials
