# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import argparse
import asyncio
import os
from signal import signal, SIGINT
import sys
import json
from asyncinit import asyncinit

from sanic import Sanic
from sanic_cors import CORS
from zmq.asyncio import ZMQEventLoop



from spf import SanicPluginsFramework


import coloredlogs, verboselogs, logging
import config
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

from data_sources import DATASOURCES_BP
from errors_module import ERRORS_BP
#from database_calls import DATABASE_BP
from users_module import USERS_BP
from backup import BACKUP_BP
import concurrent.futures
from sanic.websocket import WebSocketProtocol
from websockets.exceptions import ConnectionClosed
import string
from sanic import Blueprint
from sanic import response
import random
import time
#from secrets.aws_secret_manager import get_secrets

from data_sources.takeout.parse_emails import TakeoutEmails
import socketio

sio = socketio.AsyncServer(async_mode='sanic', ping_timeout=30, logger=False, cors_allowed_origins=["http://localhost:4200"])
app = Sanic(__name__)


app.config['CORS_AUTOMATIC_OPTIONS'] = True
cors = CORS(app)
sio.attach(app)



SOCKETS_BP = Blueprint("sockets", url_prefix="")


start_timer = None




@SOCKETS_BP.get('socks')
async def feed(request):

    # characters = list(string.ascii_uppercase)
    # while True:
    #     try:
    #         data = await ws.recv()
    #     except (ConnectionClosed):
    #         print("Connection is Closed")
    #         data = None
    #         break
        
    #     print('Received: ' + data)

    
    #     try:
    #         for _ in range(10):
    #             random.shuffle(characters)
    #             time.sleep(2)
    #             data = "".join(characters)
    #             logger.info(f"Data being sent is {data}")
    #             logger.info(f'Sending: {data}')
    #             r = await ws.send(data)
    #             logger.info(r)
    #     except ConnectionClosed:
    #         logger.error("Connection has been closed abruptly")
    
    for i in range(100):
        await request.app.config.SIO.emit('takeout', {'data': f"Progress of the takeout is {i*10}"})
        time.sleep(2)


async def background_task():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        await sio.sleep(10)
        count += 10
        await sio.emit('message', {'data': f'Progress of the app is {count}'})


@sio.event
async def my_event(sid, message):
    await sio.emit('message', {'data': message['data']}, room=sid)


@sio.event
async def my_broadcast_event(sid, message):
    await sio.emit('datapod_message', {'data': message['data']})



@sio.event
async def takeout(sid, message):
    logger.info(f"Data received is {message}")
    for i in range(0, 11):
        await sio.emit('takeout', {'data': f"Progress of the takeout is {i*10}"})
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






@app.listener('before_server_start')
async def before_start(app, uvloop):
    #sem = await  asyncio.Semaphore(100, loop=uvloop)
    logger.info("Closing database connections")
    #sio.start_background_task(background_task)

    # logger.info("Nacking outstanding messages")
    # tasks = [t for t in asyncio.all_tasks() if t is not
    #          asyncio.current_task()]

    # [task.cancel() for task in tasks]

    # logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    # await asyncio.gather(*tasks, return_exceptions=True)
    # logger.info(f"Flushing metrics")
    #app.loop = uvloop
    #app.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    return
    
@app.listener('after_server_stop')
def finish(app, loop):
    #loop.run_until_complete(app.aiohttp_session.close())
    loop.close()
    return 


def main():
    #app.blueprint(ACCOUNTS_BP)
    #app.blueprint(ERRORS_BP)
    #app.blueprint(ASSETS_BP)
    app.blueprint(DATASOURCES_BP)
    app.blueprint(ERRORS_BP)
    app.blueprint(USERS_BP)
    app.blueprint(BACKUP_BP)
    app.blueprint(SOCKETS_BP)

    #app.blueprint(UPLOAD_BP)
    #app.blueprint(USER_ACCOUNTS_BP)
    # app.blueprint(MIDDLE_LAYER)
    #zmq = ZMQEventLoop()
    #asyncio.set_event_loop(zmq)
    for _, (rule, _) in app.router.routes_names.items():
        logger.info(rule)    


    # app.config.user_data_path = config.user_data_path
    # app.config.db_dir_path = config.db_dir_path
    # app.config.archive_path = config.archive_path
    app.config.from_object(config.config_object)
    app.config["SIO"] = sio
    import pprint 
    pprint.pprint(app.config)
    #app.error_handler.add(Exception, server_error_handler)

    app.run(host="0.0.0.0", port=app.config.PORT, workers=2)

    """
    server = app.create_server(
                host=config.HOST, port=config.PORT,
                debug=config.DEBUG, access_log=True)
    #loop = asyncio.get_event_loop()

    ##not wait for the server to strat, this will return a future object
    #loop.run_until_complete(server)

   
    ##future.add_done_callback(functools.partial(db_callback, app))


    #task = asyncio.ensure_future(from_mnemonic(app.config.GOAPI_URL,
                                            #app.config.ADMIN_MNEMONIC))
    #task.add_done_callback(functools.partial(mstr_mnemic_chk_calbck, app))

    
    for _, (rule, _) in app.router.routes_names.items():
        logging.info(rule)    
   


    loop = asyncio.get_event_loop()

    loop.run_until_complete(server)
        
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop() 

   
    signal(SIGINT, lambda s, f: loop.close())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        ##close_connections(app)
        loop.stop()
    """
# async def server_error_handler(request, exception):
#     return text("Oops, server error", status=500)

if __name__ == "__main__":
    main()
