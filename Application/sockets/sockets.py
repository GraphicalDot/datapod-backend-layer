

import socketio
from loguru import logger
import time


sio = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins=[])

#sio = socketio.AsyncServer(async_mode='sanic', ping_timeout=30, logger=False, cors_allowed_origins=[])

# async def background_task():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         await sio.sleep(10)
#         count += 10
#         await sio.emit('takeout_response', {'data': f'Progress of the app is {count}'}, namespace='/takeout')





##this will only be activate if you emit a message with namespoace takeout 
##from the client side
@sio.on("initiate_takeout", namespace='/takeout')
async def  handle_initiate_takeout(sid, message):
    logger.info(f"Data received is {message}")
    for i in range(0, 11):
        logger.info(f"Progress of the takeout namespace is {i*10}")
        await sio.emit('takeout_response', {'data': f"Progress of the takeout namespace is {i*10}"}, namespace="/takeout")
        time.sleep(2)



@sio.on("initiate_takeout")
async def  handle_initiate_takeout(sid, message):
    logger.info(f"Data received is {message}")
    for i in range(0, 11):
        logger.info(f"Progress of the global namespace is {i*10}")
        await sio.emit('takeout_response', {'data': f"Progress of the / takeout is {i*10}"}, namespace="/takeout")
        time.sleep(2)


async def send_ping():
    global start_timer
    start_timer = time.time()
    await sio.emit('ping', None)


@sio.event
async def connect(sid, environ):
    print('connected to server')
    await send_ping()


@sio.event
async def pong_from_server(data):
    global start_timer
    latency = time.time() - start_timer
    print('latency is {0:.2f} ms'.format(latency * 1000))
    await sio.sleep(1)
    await send_ping()


@sio.event
async def takeout_email_parse_progress_broadcast(message):
    await sio.emit("takeout_response", {'data': message }, namespace="/takeout")

    # #broadcasts = [ws.send(message) for ws in app.ws_clients]
    # #for result in asyncio.as_completed(broadcasts):
    # try:
    #     await asyncio.wait(broadcast)
    #     logger.info(f"completed {message}")
    
    # except Exception as ex:
    #     template = f"An exception of type {ex} occurred"
    #     logger.error(template)
    # return 


@sio.event
async def broadcast(message):
    await sio.emit("takeout_response", {'data': message }, namespace="/takeout")


@sio.event
async def takeout_reser_purc_parse_progress_broadcast(message):
    await sio.emit("takeout_reser_pur_progress", {'data': message }, namespace="/takeout")