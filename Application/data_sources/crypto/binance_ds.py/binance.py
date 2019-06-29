










def initiate_client():
    client = Client(api_key, api_secret)

def get_all_tickers():
    tickers = client.get_orderbook_tickers()




def for ticker in tickers[0:10]: 
    ...:     orders = client.get_all_orders(symbol=ticker["symbol"], limit=10) 
    ...:     print (orders) 