


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase
"""
user_mentions is alos a list of dicts
'entities': {'hashtags': [{'text': 'AI', 'indices': ['31', '34']},
   {'text': 'machinelearning', 'indices': ['39', '55']}],
  'symbols': [],
  'user_mentions': [],
  'urls': [{'url': 'https://t.co/x1c6JxZ3CB',
    'expanded_url': 'http://www.forbes.com/sites/louiscolumbus/2018/02/18/roundup-of-machine-learning-forecasts-and-market-estimates-2018/',
    'display_url': 'forbes.com/sites/louiscol…',
    'indices': ['103', '126']}]
"""

def coderepos_github_initialize(db):

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
        

    class Tweet(BaseModel):
        retweeted = peewee.BooleanField(null=True)
        source = peewee.TextField(null=True) #<a href="http://twitter.com" rel="nofollow">Twitter Web Client</a>',
        entities = peewee.BlobField(null=True)
        symbols = peewee.BlobField(null=True)
        display_text_range=peewee.BlobField(null=True)
        favorite_count= peewee.TextField(null=True)
        id_str=peewee.TextField(null=True)
        possibly_sensitive = peewee.BooleanField(null=False)
        truncated=peewee.BooleanField(null=True)
        retweet_count=peewee.TextField(null=True)
        created_at=peewee.TextField(null=True),
        favorited=peewee.BooleanField(null=True),
        full_text=peewee.TextField(null=False)
        lang=peewee.TextField(null=True)
        in_reply_to_screen_name=peewee.TextField(null=True)
        in_reply_to_user_id_str=peewee.TextField(null=True)
        

    db.create_tables([
            Tweet, 
        ])

    #db.drop_tables([GitHubRepo])



    return Tweet

