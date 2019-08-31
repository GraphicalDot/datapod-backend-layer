


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

    class GitHubCreds(BaseModel):
        username = peewee.TextField(unique=True, null=False)
        password = peewee.TextField(null=False)
        

    class GitHubRepo(BaseModel):
        path = peewee.TextField(index=True, null=False)
        owner = peewee.BlobField()
        id = peewee.TextField(index=True, unique=True, null=False)
        node_id = peewee.TextField(index=True, unique=True,  null=False)
        name = peewee.TextField(null=True)
        full_name = peewee.TextField(null=True)
        private = peewee.BooleanField(null=True)
        html_url = peewee.TextField(null=True)
        git_url = peewee.TextField(null=True)
        git_pull_url = peewee.TextField(null=True) #only for gist
        git_push_url = peewee.TextField(null=True) #only for gist
        ssh_url = peewee.TextField(null=True)
        clone_url = peewee.TextField(null=True)
        forks_url = peewee.TextField(null=True)
        downloaded_at =  peewee.DateTimeField(default=datetime.datetime.now)
        description = peewee.TextField(null=True)
        fork = peewee.BooleanField(null=True)
        url = peewee.TextField(null=True)
        created_at = peewee.DateTimeField()
        updated_at = peewee.DateTimeField()
        pushed_at = peewee.DateTimeField(null=True)
        size = peewee.IntegerField(null=True)
        stargazers_count = peewee.SmallIntegerField(null=True)
        watchers_count = peewee.SmallIntegerField(null=True)
        language = peewee.TextField(null=True)
        has_issues =  peewee.BooleanField(null=True)
        has_projects  = peewee.BooleanField(null=True)
        has_downloads = peewee.BooleanField(null=True)
        has_wiki=peewee.BooleanField(null=True)
        has_pages=peewee.BooleanField(null=True)
        forks_count=peewee.SmallIntegerField(null=True)
        mirror_url= peewee.TextField(null=True)
        archived=peewee.BooleanField(null=True)
        disabled= peewee.BooleanField(null=True)
        open_issues_count= peewee.SmallIntegerField(null=True)
        license=peewee.TextField(null=True)
        forks= peewee.SmallIntegerField(null=True)
        open_issues=peewee.SmallIntegerField(null=True)
        watchers=peewee.SmallIntegerField(null=True)
        default_branch=peewee.TextField(null=True)
        is_starred=peewee.BooleanField()
        is_gist=peewee.BooleanField()

        class Meta:
            indexes = ((('id', 'node_id'), True),)

    db.create_tables([
            GitHubRepo, 
            GitHubCreds
        ])

    #db.drop_tables([GitHubRepo])



    return GitHubRepo, GitHubCreds

