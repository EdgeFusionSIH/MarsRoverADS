import asyncio
import json
import os
import websockets

BHAVIKA_IP = "172.20.10.12"
PORT = 8765

MY_FILE = "node1\\outputs\\p2pn1n2Output.json"
RECEIVED_FILE = "node1\\inputs\\p2pn1n2Input.json"


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
                print("Sent Tiyas's data:", data)

        except Exception as e:
            print("Send error:", e)

        await asyncio.sleep(0.1)


async def receive_data(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)

            with open(RECEIVED_FILE, "w") as file:
                json.dump(data, file, indent=4)

            print("Received Bhavika's data:", data)

        except Exception as e:
            print("Receive error:", e)


async def main():
    uri = f"ws://{BHAVIKA_IP}:{PORT}"

    print("Connecting to Bhavika...")

    async with websockets.connect(uri) as websocket:
        print("Connected to Bhavika!")

        await asyncio.gather(
            send_my_file(websocket),
            receive_data(websocket)
        )


asyncio.run(main())