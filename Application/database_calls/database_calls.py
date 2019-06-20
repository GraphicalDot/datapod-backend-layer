
#from playhouse.sqlite_ext import SqliteExtDatabase
import peewee
import datetime



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
    db = peewee.SqliteDatabase(path)


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
        password = peewee.CharField()
        mnemonic = peewee.TextField(null=True)
        id_token = peewee.BlobField(null= True)
        access_token = peewee.BlobField(null= True)
        refresh_token = peewee.BlobField(null= True)


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

                # create a non-unique on from/to
                (('from_addr', 'to_addr'), False),
            )



    db.create_tables([
        Logs,
        Backups,
        Credentials,
        Emails
        ])
    # for person in Logs.select().dicts():
    #     print(person.message)
    for person in Credentials.select().dicts():
        print(person)

    return Logs, Backups, Credentials, Emails


