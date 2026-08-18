import asyncio
import json
import os
import websockets

HOST = "0.0.0.0"
PORT = 8765

MY_FILE = "node2/outputs/p2pn1n2Output.json"
RECEIVED_FILE = "node2/inputs/p2pn1n2Input.json"


async def send_my_file(websocket):
    last_modified = 0

    while True:
        try:
            modified = os.path.getmtime(MY_FILE)

            if modified != last_modified:
                last_modified = modified

                with open(MY_FILE, "r") as file:
                    data = json.load(file)

                await websocket.send(json.dumps(data))
                print("Sent Bhavika's data:", data)

        except Exception as e:
            print("Send error:", e)

        await asyncio.sleep(0.1)


async def receive_data(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)

            with open(RECEIVED_FILE, "w") as file:
                json.dump(data, file, indent=4)

            print("Received Tiyas's data:", data)

        except Exception as e:
            print("Receive error:", e)


async def handler(websocket):
    print("Tiyas connected!")

    await asyncio.gather(
        send_my_file(websocket),
        receive_data(websocket)
    )


async def main():
    async with websockets.serve(handler, HOST, PORT):
        print("WebSocket server running on port 8765")
        await asyncio.Future()


asyncio.run(main())