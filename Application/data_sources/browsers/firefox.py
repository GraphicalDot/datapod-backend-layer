
import os
import sqlite3
import tldextract
import collections
import urlparse

extract = lambda e : tldextract.extract(e[0]) 

def firefox_history(path):
    data_path = os.path.expanduser('~')+"/.mozilla/firefox/0mttxac9.default"
    files = os.listdir(data_path)
    history_db = os.path.join(data_path, 'places.sqlite')
    c = sqlite3.connect(history_db)
    cursor = c.cursor()
    select_statement = "select moz_places.url, moz_places.visit_count from moz_places;"
    cursor.execute(select_statement)
    results = cursor.fetchall()
    for url, count in results:
        print(url)




def get_most_visited(url_list, number):
    counter=collections.Counter([extract(e).domain for e in url_list]) 
    return counter.most_common(number) 


def get_g_queries(url_list):
    google_urls = [e for e in url_list if e[0].startswith("https://www.google.com/search?")] 
    for query in google_urls:
        f = urlparse(query[0]) 
        print (f.query) 

