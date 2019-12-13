

import abc
from dataclasses import dataclass, field
import os
from typing import List, Tuple, Any
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel
import sqlite3


@dataclass
class Base(abc.ABC):
    __slots__ = ['directory']

    directory: str 
    path: str= field(init=False) 
    pragmas: List[Tuple[str, Any]] = field(init=False)
    db_object: Any = field(init=False)

    def __post_init__(self):
        self.path = os.path.join(self.directory, "plugins", self.plugin_name)
        self.pragmas = [('journal_mode', 'wal2'),('cache_size', -1024*64)]
        self.db_object = SqliteExtDatabase(os.path.join(self.path, f"{self.plugin_name}.db"), pragmas=self.pragmas,  detect_types=sqlite3.PARSE_DECLTYPES)


    @abc.abstractmethod
    def process(self) -> str:
        pass

    @abc.abstractmethod
    def routes(self) -> tuple:
        pass


@dataclass
class Plugin(Base):
    plugin_name: str = "Default"


    def __post_init__(self):
        super().__post_init__()
        
    def routes(self) -> tuple:
        pass

    def process(self) -> str:
        return f"{self.a} {self.b}"



if __name__ == "__main__":
    implemented_instance = Plugin("~/.datapod", plugin_name="uber")
    # assert isinstance(implemented_instance, Base)
    print (implemented_instance.path)
    print (implemented_instance.pragmas)
    print (implemented_instance.db_object)
