


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
        id = peewee.TextField(index=True, null=False)
        node_id = peewee.TextField(index=True, null=False)
        name = peewee.TextField(null=True)
        full_name = peewee.TextField(null=True)
        private = peewee.BooleanField(null=True)
        html_url = peewee.TextField()
        git_url = peewee.TextField(null=True)
        git_pull_url = peewee.TextField(null=True) #only for gist
        git_push_url = peewee.TextField(null=True) #only for gist
        ssh_url = peewee.TextField()
        clone_url = peewee.TextField()
        forks_url = peewee.TextField()
        downloaded_at =  peewee.DateTimeField(default=datetime.datetime.now)
        description = peewee.TextField(null=True)
        fork = peewee.BooleanField(null=True)
        url = peewee.TextField()
        created_at = peewee.DateTimeField()
        updated_at = peewee.DateTimeField()
        pushed_at = peewee.DateTimeField()
        size = peewee.IntegerField(null=True)
        stargazers_count = peewee.SmallIntegerField()
        watchers_count = peewee.SmallIntegerField()
        language = peewee.TextField(null=True)
        has_issues =  peewee.BooleanField(null=True)
        has_projects  = peewee.BooleanField(null=True)
        has_downloads = peewee.BooleanField(null=True)
        has_wiki=peewee.BooleanField(null=True)
        has_pages=peewee.BooleanField(null=True)
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
        is_gist=peewee.BooleanField()

        class Meta:
            indexes = ((('id', 'node_id'), True),)

    db.create_tables([
            GitHubRepo
        ])

    #db.drop_tables([GitHubRepo])



    return GitHubRepo

