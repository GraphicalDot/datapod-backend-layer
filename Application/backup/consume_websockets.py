import asyncio
import websockets

async def hello():
    async with websockets.connect('wss://localhost:8000/backup/make_backup') as websocket:
        #await websocket.send('{"type":"listen_start", "device_id":1110,"id": "2098388936"}')
        greeting = await websocket.recv()
        print(greeting)

asyncio.get_event_loop().run_until_complete(hello())