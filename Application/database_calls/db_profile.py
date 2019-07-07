
#-*- coding:utf-8 -*-

"""
Deals witht he db calls for the landing page of the desktop app of datapod

"""


import json
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def store_datasource(**data):
    try:
        data_sources_table = data["tbl_object"]

        entry = (data_sources_table.insert(source=data["source"],  
                                    message=data["message"],
                                    name=data["name"]
                                    )
           .on_conflict_replace()
           .execute())

        logger.success(f"Success, Datasources, On  update for {data['source']}, result {entry}")
    except Exception as e:
        logger.error(f"Error, Datasources, Couldnt update {data['source']} because of {e}")
    return 


def get_datasources(datasource_tbl):
    """
        for tweet in Tweet.select().where(Tweet.created_date < datetime.datetime(2011, 1, 1)):
         print(tweet.message, tweet.created_date)

    """
    query = (datasource_tbl
                .select()
                .dicts())
    return list(query)


def count_datasources(datasource_tbl):
    """
    """
    query = (datasource_tbl
                .select()
                .count())
    return query


