


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase


def initialize(db):

    class BaseModel(peewee.Model):
        class Meta:
            database = db




    class Permissions(BaseModel):
        plugin_name = peewee.TextField(index=True, null=False)
        datasource_name = peewee.TextField(null=False, index=True)
        table_name = peewee.TextField(null=False)
        timestamp = peewee.DateTimeField(default=datetime.datetime.now)

        class Meta:
            indexes = (
                        (('plugin_name', 'datasource_name'), True),
                    )

    class Tablenames(BaseModel):
        datasource_name = peewee.TextField(null=False, index=True)
        table_name = peewee.TextField(null=False)
        display_name = peewee.TextField(null=False)
        
        class Meta:
            indexes = (
                        (('table_name', 'datasource_name'), True),
                    )

    


    db.create_tables([
            Permissions,
            Tablenames
        ])

    db.drop_tables([  
            # Creds,
            # Archives, 
            # Images,
            # YourPosts,
            # OtherPosts,
            # Content,
            # Status

        ])



    return Permissions, Tablenames
