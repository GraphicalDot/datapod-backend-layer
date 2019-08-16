


import peewee
import datetime
import sqlite3

from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
#from playhouse.apsw_ext import APSWDatabase


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

    class GitHubRepo(BaseModel):
        path = peewee.TextField(index=True, null=False)
        owner = peewee.BlobField()
        id = peewee.IntegerField(null=False)
        node_id = peewee.TextField()
        name = peewee.TextField(index=True, null=False)
        full_name = peewee.TextField()
        private = peewee.BooleanField()
        html_url = peewee.TextField()
        git_url = peewee.TextField()
        ssh_url = peewee.TextField()
        clone_url = peewee.TextField()
        forks_url = peewee.TextField()
        downloaded_at =  peewee.DateTimeField(default=datetime.datetime.now)
        description = peewee.TextField(null=True)
        fork = peewee.BooleanField()
        url = peewee.TextField()
        created_at = peewee.DateTimeField()
        updated_at = peewee.DateTimeField()
        pushed_at = peewee.DateTimeField()
        size = peewee.IntegerField()
        stargazers_count = peewee.SmallIntegerField()
        watchers_count = peewee.SmallIntegerField()
        language = peewee.TextField(null=True)
        has_issues =  peewee.BooleanField()
        has_projects  = peewee.BooleanField()
        has_downloads = peewee.BooleanField()
        has_wiki=peewee.BooleanField()
        has_pages=peewee.BooleanField()
        forks_count=peewee.SmallIntegerField()
        mirror_url= peewee.TextField(null=True)
        archived=peewee.BooleanField()
        disabled= peewee.BooleanField()
        open_issues_count= peewee.SmallIntegerField()
        license=peewee.TextField(null=True)
        forks= peewee.SmallIntegerField()
        open_issues=peewee.SmallIntegerField()
        watchers=peewee.SmallIntegerField()
        default_branch=peewee.TextField()
        is_starred=peewee.BooleanField()

        class Meta:
            indexes = ((('id', 'name'), True),)

    db.create_tables([
            GitHubRepo
        ])

    #db.drop_tables([GitHubRepo])



    return GitHubRepo

