import pytz
import datetime


def timezone_timestamp(naive_timestamp, timezone):
    tz_kolkata = pytz.timezone(timezone)
    time_format = "%Y-%m-%d %H:%M:%S"
    if naive_timestamp:
        aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp))
    else:
        naive_timestamp = datetime.datetime.now()
        aware_timestamp = tz_kolkata.localize(naive_timestamp)
    return aware_timestamp


def month_aware_time_stamp(naive_timestamp=None): 
     tz_kolkata = pytz.timezone('Asia/Kolkata') 
     time_format = "%Y-%m-%d %H:%M:%S" 
     if naive_timestamp: 
         aware_timestamp = tz_kolkata.localize(datetime.datetime.fromtimestamp(naive_timestamp)) 
     else: 
         naive_timestamp = datetime.datetime.now() 
         aware_timestamp = tz_kolkata.localize(naive_timestamp) 
     return {"timestamp": aware_timestamp.strftime(time_format + " %Z%z"), "year": aware_timestamp.year, "month": aware_timestamp.month} 


