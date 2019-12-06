
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



    class Permission(BaseModel):
        plugin_name = peewee.TextField(index=True)
        plugin_dir = peewee.TextField(null=True, unique=True)
        tables = peewee.TextField(null=True)
        last_updated =  peewee.DateTimeField(default=datetime.datetime.now)




    result = db.create_tables([
        Permission
        ])

    return Permission

