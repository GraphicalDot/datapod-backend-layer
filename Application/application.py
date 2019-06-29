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
 

#from secrets.aws_secret_manager import get_secrets

app = Sanic(__name__)
CORS(app, automatic_options=True)

@app.listener('before_server_start')
async def before_start(app, uvloop):
    sem = await asyncio.Semaphore(100, loop=uvloop)




def main():
    #app.blueprint(ACCOUNTS_BP)
    #app.blueprint(ERRORS_BP)
    #app.blueprint(ASSETS_BP)
    app.blueprint(DATASOURCES_BP)
    app.blueprint(ERRORS_BP)
    app.blueprint(USERS_BP)
    app.blueprint(BACKUP_BP)

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
    import pprint 
    pprint.pprint(app.config)
    #app.error_handler.add(Exception, server_error_handler)

    app.run(host="0.0.0.0", port=8000)

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
