


from .db_initialize import initialize
from .api import sample_get, sample_post
import os
from .variables import DATASOURCE_NAME
import peewee
import datetime




@dataclass
class Plugin(Base):
    plugin_name: str = "uber"


    def __post_init__(self):
        super().__post_init__()
        
    def routes(self) -> Dict[str, List]:
        return {"GET": [("sample_get", sample_get)], 
                    "POST": [("sample_post", sample_post)]} 
        

    def process(self) -> str:
        return f"{self.a} {self.b}"






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

    return {"permission": Permission}


