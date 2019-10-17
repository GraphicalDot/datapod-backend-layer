
#from playhouse.sqlite_ext import SqliteExtDatabase
import peewee
import datetime
import sqlite3
from loguru import logger


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



    class Email(BaseModel):
        username = peewee.TextField(index=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField(index=True, null=False)

        email_id = peewee.TextField(unique=True)
        email_id_raw = peewee.TextField(unique=True)
        from_addr = peewee.CharField()
        to_addr = peewee.CharField()
        subject = peewee.TextField()
        message_type = peewee.CharField()
        content = peewee.TextField()
        date = peewee.DateTimeField()
        path = peewee.TextField()
        attachments = peewee.BooleanField()
        
        class Meta:
            indexes = (
                   # create a unique on from/to/date
                (('username', 'from_addr', 'to_addr', 'date'), True),
                (('from_addr', 'to_addr'), False),
            )





    class IndexEmailContent(FTSModel):
        username = peewee.TextField()
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()
        content = peewee.TextField()
        email_id = peewee.TextField()
        content_hash = peewee.TextField()
        class Meta:
            database = db

    
    # class EmailAttachments(BaseModel):
    #     email = peewee.ForeignKeyField(Email, backref='tweets')

    class EmailAttachment(BaseModel):
        username = peewee.TextField()
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()
    
        email_id = peewee.TextField(unique=False, index=True)
        path = peewee.TextField()
        attachment_name = peewee.TextField()
        date = peewee.DateTimeField()
        message_type = peewee.CharField()


    class Images(BaseModel):
        username = peewee.TextField(index=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()
        
        creation_time = peewee.DateTimeField(index=True, null=False)
        modification_time = peewee.DateTimeField(index=True, null=False)
        photo_taken_time = peewee.DateTimeField(index=True, null=False)
        description = peewee.TextField(null=True)
        url = peewee.TextField(null=True)
        title = peewee.TextField(null=False, index=True)
        image_path = peewee.TextField( null=False)
        geo_data = peewee.BlobField(null=True)
        class Meta:
            indexes = (
                # create a unique on from/to/date
                (('username', 'creation_time', 'title'), True),
            )

    

    class Purchases(BaseModel):
        username = peewee.TextField(index=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()

        merchant_name = peewee.CharField(index=True, null=False)
        products = peewee.BlobField(index=True, null=False)
        time = peewee.DateTimeField(index=True, null=False)
        class Meta:
            indexes = (
            # create a unique on from/to/date
            (('products', 'time', 'merchant_name'), True),

            )
    
    class Reservations(BaseModel):
        username = peewee.TextField(index=True, null=False)
        datapod_timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        checksum = peewee.TextField()

        merchant_name = peewee.CharField(index=True, null=False)
        dest = peewee.CharField(index=True, null=False)
        src = peewee.CharField(index=True, null=False)
        time = peewee.DateTimeField(index=True, null=False)
        class Meta:
            indexes = (
            # create a unique on from/to/date
            (('dest', 'src', 'time', 'merchant_name'), True),

            )
    




    result = db.create_tables([
        Creds,
        Status,
        Stats,
        Email,
        EmailAttachment,
        IndexEmailContent,
        Images,
        Purchases,
        Reservations, 
        Archives
        ])

    return Creds, \
        Status, \
        Stats,\
        Email, \
        EmailAttachment,\
        IndexEmailContent,\
        Images,\
        Purchases,\
        Reservations, \
        Archives 


