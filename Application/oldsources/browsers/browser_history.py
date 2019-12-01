import os
import sqlite3
import asyncio
import aiohttp
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
import os
from errors_module.errors import APIBadRequest
import tldextract
import collections
from urllib.parse import urlparse 
from loguru import logger



BROWSER_HISTORY_BP = Blueprint("browser_history", url_prefix="/browser_history")

extract = lambda e : tldextract.extract(e) 

def get_most_visited(url_list, number):
    counter=collections.Counter([extract(e).domain for e in url_list]) 
    return counter.most_common(number) 


def get_g_queries(url_list):
    google_urls = [e for e in url_list if e[0].startswith("https://www.google.com/search?")] 
    for query in google_urls:
        f = urlparse(query[0]) 
        print (f.query) 


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise APIBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise Exception("Improper JSON format")




@BROWSER_HISTORY_BP.get('/firefox')
def firefox_history(request):
    data_path = os.path.expanduser('~')+"/.mozilla/firefox/"
    for data_dir in os.listdir(data_path):
        if data_dir.endswith("default"): 
            break

    if not data_dir:
        raise APIBadRequest("Firefox is not installed")
    data_dir = os.path.join(data_path, data_dir) 
    history_db = os.path.join(data_dir, 'places.sqlite')
    logger.info(f"History db is {history_db}")
    c = sqlite3.connect(history_db)
    cursor = c.cursor()
    select_statement = "select moz_places.url, moz_places.visit_count from moz_places;"
    select_statement = "select * from moz_places;"
    cursor.execute(select_statement)
    results = cursor.fetchall()

    queries = []    
    for e in results:
        if e[2]:
            queries.append(e[2])
    result = get_most_visited([e[1] for e in results],  50)

    x_axis, y_axis = list(zip(*result))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"most_searched": {"x_axis": x_axis, "y_axis": y_axis}, "queries": queries}
        })


@BROWSER_HISTORY_BP.get('/chrome')
def chrome_history(request):
    data_path = os.path.expanduser('~')+"/.config/google-chrome/"
    data_dir = "Default"

    data_dir = os.path.join(data_path, data_dir) 
    history_db = os.path.join(data_dir, 'History')
    if not os.path.exists(history_db):
        raise APIBadRequest("Chrome is not installed")

    logger.info(f"History db is {history_db}")
    c = sqlite3.connect(history_db)
    cursor = c.cursor()
    select_statement = "select url, title, visit_count, last_visit_time from urls;"
    try:
        cursor.execute(select_statement)
    except sqlite3.OperationalError:
        raise APIBadRequest("Database is locked, Please close chrome browser and try again")

    results = cursor.fetchall()
    for r in results:
        print(r)
    result = get_most_visited([e[0] for e in results],  50)
    queries = []    
    for e in results:
        if e[1]:
            queries.append(e[1])
    
    x_axis, y_axis = list(zip(*result))
    return response.json(
        {
        'error': False,
        'success': True,
        "data": {"most_searched": {"x_axis": x_axis, "y_axis": y_axis}, "queries": queries}
        })





