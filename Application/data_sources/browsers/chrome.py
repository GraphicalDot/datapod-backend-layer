import os
import sqlite3
con = sqlite3.connect('/home/manivannan/.config/google-chrome/Default/History')
c = con.cursor()
c.execute("select url, title, visit_count, last_visit_time from urls") #Change this to your prefered query
results = c.fetchall()
for r in results:
    print(r)
