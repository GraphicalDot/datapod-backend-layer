
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




    db.create_tables([
        Logs,
        Backups
        ])