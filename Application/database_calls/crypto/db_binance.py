#-*- coding: utf-8 -*-
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def store(tbl_obj, api_key, api_secret):
    try:
        tbl_obj.insert(exchange="binance",  
                        api_key=api_key,
                        api_secret=api_secret)\
            .on_conflict_replace()\
            .execute()

        logger.success(f"On insert the credentials for binance exchange")
    except Exception as e:
        logger.error(f"Couldnt save creds data for binanace exchange because of {e}")
    return 


def get_creds(tbl_obj):
    print (tbl_obj)
    try:
        res = tbl_obj.select().where(tbl_obj.exchange=="binance").get()
        return res.api_key, res.api_secret
    except Exception as e:
        logger.error(f"Couldnt fetch creds data for binanace exchange because of {e}")
    return


def store_pairs(db_object, tbl_obj, pair_orders):
    try:
        with db_object.atomic():
            # insert data
            for order in pair_orders:
                interm = {}
                interm.update({
                        "symbol": order['symbol'], 
                        "order_id": order['orderId'], 
                        "client_order_id": order['clientOrderId'], 
                        "price": order['price'], 
                        "orig_qty": order['origQty'], 
                        "executed_qty": order['executedQty'], 
                        "cummulative_quote_qty": order['cummulativeQuoteQty'], 
                        "status" : order['status'], 
                        "time_in_force": order['timeInForce'], 
                        "_type" : order['type'], 
                        "side": order['side'], 
                        "stop_price": order['stopPrice'], 
                        "iceberg_qty": order['icebergQty'], 
                        "time": order['time'], 
                        "update_time": order['updateTime'], 
                        "is_working": order['isWorking']})
                tbl_obj.create(**interm)
                logger.success(f"success in inserting {order['symbol']}")

    except Exception as e:
        logger.error(f"Couldnt store binance order pair {order['symbol']} because of {e}")

    return 