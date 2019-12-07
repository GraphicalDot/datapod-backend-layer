

"""
class User(Model):
    username = CharField()
    join_date = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField()
User.delete() # would delete all users in the database
delete_instance() is a instance method, that will delete the database row represented by an instance of a Model subclass.
me = User.create(username="myers") # create a new user with my username
me.delete_instance() # delete me from the database
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


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel


def initialize(db):
    
    class BaseModel(peewee.Model):
        class Meta:
            database = db



    class Backups(BaseModel):
        timestamp = peewee.DateTimeField(default=datetime.datetime.now)
        Level = peewee.SmallIntegerField()
        success = peewee.BooleanField()


    class Status(BaseModel):
        status = peewee.TextField(null=True)
        last_updated =  peewee.DateTimeField(default=datetime.datetime.now)
        path = peewee.TextField(null=True)
        original_path = peewee.TextField(null=True)
        checksum = peewee.TextField(index=True, null=True)
        percentage = peewee.IntegerField(null=True)

        
    class Stats(BaseModel):
        data_items = peewee.IntegerField(null=True)
        disk_space_used = peewee.TextField(null=True)
        sync_frequency = peewee.TextField(null=True)
        sync_type = peewee.TextField(null=True)
        last_sync = peewee.DateTimeField(default=datetime.datetime.now)
        next_sync = peewee.DateTimeField(default=datetime.datetime.now)




    result = db.create_tables([
        Backups,
        Status,
        Stats
        ])

    return Backups, Status, Stats
