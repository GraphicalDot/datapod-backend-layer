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
import importlib
from sanic import Sanic
from sanic_cors import CORS
from zmq.asyncio import ZMQEventLoop

import pprint 


from spf import SanicPluginsFramework


import config


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
  
from sanic.response import json, json_dumps
from sanic.exceptions import abort
from sanic_sse import Sse
from http import HTTPStatus
#from sockets.sockets import sio
#from loguru import logger
#from custom_logger import logger
#from secrets.aws_secret_manager import get_secrets
from database_calls.credentials import update_datasources_status
from loguru import logger
#from custom_logger import LOGGING

from sentry_sdk import init
init("https://252ce7f1254743cda2f8c46edda42044@sentry.io/1763079")

app = Sanic(__name__)

# app.config['CORS_AUTOMATIC_OPTIONS'] = True
# app.config['CORS_SUPPORTS_CREDENTIALS'] = True
#app.config['CORS_ALLOW_CREDENTIALS'] = True

##cors = CORS(app, resources={r"*": {"origins": "*"}})
app.config['CORS_SUPPORTS_CREDENTIALS'] = True

CORS(app, resources={r"/*": {"origins": "*"}}, automatic_options=True)


#sio.attach(app)




SOCKETS_BP = Blueprint("sockets", url_prefix="")


start_timer = None





  


async def before_sse_request(request):
    if request.headers.get("Auth", "") != "some_token":
        pass
        #abort(HTTPStatus.UNAUTHORIZED, "Bad auth token")


#sanic_app = Sanic()

# The default sse url is /sse but you can set it via init argument url.
Sse(
    app, url="/events", before_request_func=before_sse_request
)  # or you can use init_app method




@SOCKETS_BP.post('send')
async def send_event(request):

    # if channel_id is None than event will be send to all subscribers
    channel_id = request.json.get("channel_id")
    logger.success(f"Message {request.json} on {channel_id}")

    # optional arguments: event_id - str, event - str, retry - int
    # data should always be str
    # also you can use sse_send_nowait for send event without waiting
    try:
        await request.app.sse_send(json_dumps(request.json), channel_id=channel_id)
    except KeyError:
        logger.error("channel not found, No subscribers found")
        return json({"error": True, 
                    "succes": False,
                    "message": "No subscribers found"})

    return json({"error": False, 
                    "succes": True,
                    "message": "subscribers found and message sent"})
    



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


def add_routes(app):
    import datasources
    import pkgutil
    list_name = []
    for finder, name, ispkg in pkgutil.iter_modules(datasources.__path__):
        if name.startswith('datapod_'):
            logger.success(f"Reading module {name}")
            module_name = f"datasources.{name}.settings"
            m = importlib.import_module(module_name)

            inst = m.Routes(app.config["DB_OBJECT"])
            # logger.info(inst.config)
            # logger.info(inst.routes)
            # module_name = __import__(name)
            # logger.info("module_name")
            for (http_method, route_list) in inst.routes.items():
                for (route_name, handler_function) in route_list:
                    logger.info(f"Registering {http_method} for {route_name} for datasource {inst.datasource_name}")
                    app.add_route(handler_function, f'/datasources/{inst.datasource_name}/{route_name}', methods=[http_method])

            logger.info(f"Updating Appication config with {inst.datasource_name} configurations ")
            app.config.update({inst.datasource_name: inst.config})


    






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



    # app.config.user_data_path = config.user_data_path
    # app.config.db_dir_path = config.db_dir_path
    # app.config.archive_path = config.archive_path
    app.config.from_object(config.config_object)
    
    add_routes(app)

    for _, (rule, _) in app.router.routes_names.items():
        logger.info(rule)    


    logger.info(f"This is Version number {config.config_object.VERSION}")
    #app.config["SIO"] = sio
    pprint.pprint(app.config)
    #app.error_handler.add(Exception, server_error_handler)

    app.run(host="0.0.0.0", port=app.config.PORT, workers=1, access_log=True)

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

