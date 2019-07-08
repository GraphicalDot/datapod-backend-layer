
#!/usr/bin/env python3
#-*- coding:utf-8 -*-


import datetime 
import humanize

def esio():
    theday = humanize.naturalday(datetime.datetime.now() - datetime.timedelta(days=1))
    print(f"Hello World! {theday}")

if __name__ == "__main__":
    esio()