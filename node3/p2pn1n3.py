import asyncio
import json
import os
import websockets

HOST = "0.0.0.0"
PORT = 8767

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MY_FILE = os.path.join(BASE_DIR, "outputs", "p2pn1n3Output.json")
RECEIVED_FILE = os.path.join(BASE_DIR, "inputs", "p2pn1n3Input.json")
RECEIVED_IMAGE = os.path.join(BASE_DIR, "inputs", "lastFrame.jpg")

async def send_my_file(websocket):
    while True:
        try:
            if os.path.exists(MY_FILE):
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
            if isinstance(message, bytes):
                os.makedirs(os.path.dirname(RECEIVED_IMAGE), exist_ok=True)
                with open(RECEIVED_IMAGE, "wb") as f:
                    f.write(message)
                print("Received and saved lastFrame.jpg")
            else:
                data = json.loads(message)
                os.makedirs(os.path.dirname(RECEIVED_FILE), exist_ok=True)
                with open(RECEIVED_FILE, "w") as file:
                    json.dump(data, file, indent=4)
                print("Received node1's data:", data)
        except Exception as e:
            print("Receive error:", e)

async def handler(websocket):
    print("node1 connected!")
    await asyncio.gather(
        send_my_file(websocket),
        receive_data(websocket)
    )

async def main():
    async with websockets.serve(handler, HOST, PORT):
        print("WebSocket server running on port 8767")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
