import pytz
import datetime
import dateutil
from jose import jwt, JWTError 
import aiohttp
import asyncio
from loguru import logger
import os
from functools import partial

def creation_date(filename):
    time_format = "%Y-%m-%d %H:%M:%S"
    t = os.path.getctime(filename)
    return datetime.datetime.fromtimestamp(t).strftime(time_format)

def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


def modification_date(filename):
    time_format = "%Y-%m-%d %H:%M:%S"
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t).strftime(time_format)
def creation_date(filename):
    time_format = "%Y-%m-%d %H:%M:%S"
    t = os.path.getctime(filename)
    return datetime.datetime.fromtimestamp(t).strftime(time_format)



def modification_date(filename):
    time_format = "%Y-%m-%d %H:%M:%S"
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t).strftime(time_format)