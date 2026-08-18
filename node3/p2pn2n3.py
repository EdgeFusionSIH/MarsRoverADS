import asyncio
import json
import os
import websockets

HOST = "0.0.0.0"
PORT = 8766

MY_FILE = "node3/outputs/p2pn2n3Output.json"
RECEIVED_FILE = "node3/inputs/p2pn2n3Input.json"

async def send_my_file(websocket):
    last_modified = 0
    while True:
        try:
            if os.path.exists(MY_FILE):
                modified = os.path.getmtime(MY_FILE)
                if modified != last_modified:
                    last_modified = modified
                    with open(MY_FILE, "r") as file:
                        data = json.load(file)
                    await websocket.send(json.dumps(data))
                    print("Sent node3 data:", data)
        except Exception as e:
            print("Send error:", e)
        await asyncio.sleep(0.1)

async def receive_data(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
            os.makedirs(os.path.dirname(RECEIVED_FILE), exist_ok=True)
            with open(RECEIVED_FILE, "w") as file:
                json.dump(data, file, indent=4)
            print("Received node2's data:", data)
        except Exception as e:
            print("Receive error:", e)

async def handler(websocket):
    print("node2 connected!")
    await asyncio.gather(
        send_my_file(websocket),
        receive_data(websocket)
    )

async def main():
    async with websockets.serve(handler, HOST, PORT):
        print("WebSocket server running on port 8766")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())