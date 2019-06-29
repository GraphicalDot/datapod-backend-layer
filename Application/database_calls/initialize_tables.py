
#from playhouse.sqlite_ext import SqliteExtDatabase
import peewee
import datetime
import sqlite3


"""
http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#schema-migrations
pubdate_field = DateTimeField(null=True)
comment_field = TextField(default='')

# Run the migration, specifying the database table, field name and field.
migrate(
    migrator.add_column('comment_tbl', 'pub_date', pubdate_field),
    migrator.add_column('comment_tbl', 'comment', comment_field),
)

http://docs.peewee-orm.com/en/latest/peewee/querying.html#updating-existing-records
Update query uery = Stat.update(counter=Stat.counter + 1).where(Stat.url == request.url)
"""



def intialize_db(path):
    db = peewee.SqliteDatabase(path,  detect_types=sqlite3.PARSE_DECLTYPES)


    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Logs(BaseModel):
        timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        message = peewee.TextField()
        error = peewee.BooleanField()
        success = peewee.BooleanField()

    class Backups(BaseModel):
        timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        Level = peewee.SmallIntegerField()
        success = peewee.BooleanField()

    class Credentials(BaseModel):

        username = peewee.CharField(unique=True)
        mnemonic = peewee.TextField(null=True)
        id_token = peewee.BlobField(null= True)
        access_token = peewee.BlobField(null= True)
        password_hash = peewee.TextField(null= True)
        refresh_token = peewee.BlobField(null= True)
        salt = peewee.TextField(null= True)

    class Emails(BaseModel):
        email_id = peewee.CharField(unique=True)
        from_addr = peewee.CharField()
        to_addr = peewee.CharField()
        subject = peewee.TextField()
        content = peewee.TextField()
        attachments = peewee.BareField()
        date = peewee.DateTimeField()

        class Meta:
            indexes = (
                   # create a unique on from/to/date
                (('from_addr', 'to_addr', 'date'), True),
                (('from_addr', 'to_addr'), False),
            )


    class Images(BaseModel):
        source = peewee.TextField(null=True)
        creation_time = peewee.DateTimeField(index=True, null=False)
        modification_time = peewee.DateTimeField(index=True, null=False)
        photo_taken_time = peewee.DateTimeField(index=True, null=False)
        description = peewee.TextField(null=True)
        url = peewee.TextField(null=False, index=True)
        title = peewee.TextField(null=False, index=True)
        geo_data = peewee.BareField()
        image_path = peewee.TextField(null=True)
        class Meta:
            indexes = (
                # create a unique on from/to/date
                (('creation_time', 'url', 'title'), True),
            )

        
   

    class Purchases(BaseModel):
        merchant_name = peewee.CharField(index=True, null=False)
        products = peewee.CharField(index=True, null=False)
        source = peewee.CharField(index=True, null=False)
        time = peewee.DateTimeField(index=True, null=False)
        class Meta:
            indexes = (
            # create a unique on from/to/date
            (('products', 'time', 'merchant_name'), True),

            )
    
    class CryptoCreds(BaseModel):
        exchange = peewee.CharField(index=True, null=False)
        api_key = peewee.CharField(index=True, null=False)
        api_secret = peewee.CharField(index=True, null=False)
    
    class CryptoExgBinance(BaseModel):
        symbol =peewee.CharField(index=True, null=False)
        order_id = peewee.IntegerField()
        client_order_id = peewee.CharField(null=False)
        price = peewee.CharField(null=False)
        orig_qty = peewee.CharField(null=False)
        executed_qty = peewee.CharField(null=False)
        cummulative_quote_qty = peewee.CharField(index=True, null=False)
        status = peewee.CharField(index=True, null=False)
        time_in_force = peewee.CharField(null=False)
        _type= peewee.CharField(null=False)
        side= peewee.CharField(null=False)
        stop_price = peewee.CharField(index=True, null=False)
        iceberg_qty = peewee.CharField(null=False)
        time = peewee.DateTimeField(index=True, null=False)
        update_time = peewee.DateTimeField(index=True, null=False)
        is_working = peewee.BooleanField(null=False)
        class Meta:
            indexes = (
            # create a unique on from/to/date
            (('symbol', 'status', 'time'), True),

            )


    result = db.create_tables([
        Logs,
        Backups,
        Credentials,
        Emails,
        Purchases,
        Images,
        CryptoCreds,
        CryptoExgBinance
        ])
    # for person in Logs.select().dicts():
    #     print(person.message)
    print (result)
    for person in Credentials.select().dicts():
        print(person)
    print ("\n\n")

    for person in CryptoCreds.select().dicts():
        print(person)



    return Logs, Backups, Credentials, Emails, Purchases, Images, CryptoCreds,\
        CryptoExgBinance


