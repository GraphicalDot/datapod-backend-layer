import socketio
import asyncio
import time
loop = asyncio.get_event_loop()

sio = socketio.AsyncClient()
start_timer = None

#sio = socketio.Client()

@sio.event
def connect():
    print('client connection established')
    print('my sid is', sio.sid)


@sio.event
def datapod_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})

@sio.event
def my_event(data):
    print('My Event from server')



@sio.event
def message(data):
    print(f'Data from the server is {data}')



@sio.event
async def takeout(data):
    print(f'Data from Takeout {data}')
    



@sio.event
def ping(data):
    print('pING RECEIVED FROM THE SERVER from server')

@sio.event
def disconnect():
    print('disconnected from server')



async def send_ping():
    global start_timer
    start_timer = time.time()
    await sio.emit('ping_from_client')


@sio.event
async def connect():
    print('connected to server')
    await send_ping()


@sio.event
async def pong_from_server(data):
    global start_timer
    latency = time.time() - start_timer
    print('latency is {0:.2f} ms'.format(latency * 1000))
    await sio.sleep(1)
    await send_ping()


async def start_client():
    await sio.connect('http://localhost:8000')
    await sio.emit('takeout', {'data': "Progress of the takeout is scasca"})
    await sio.wait()



if __name__ == '__main__':
    loop.run_until_complete(start_client())
