
#from playhouse.sqlite_ext import SqliteExtDatabase
import peewee
import datetime

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

        username = peewee.CharField()
        password = peewee.CharField()
        mnemonic = peewee.TextField()
        id_token = peewee.BlobField()

    class Emails(BaseModel):
        email_id = peewee.CharField()
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
    for person in Logs.select():
        print(person.message)

    return Logs, Backups, Credentials, Emails


