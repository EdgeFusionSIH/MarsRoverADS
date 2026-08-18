import asyncio
import json
import os
import websockets

NODE3_IP = "172.20.10.9" #library test aug 18 10:10 PM aarav phone hotspot
PORT = 8766

MY_FILE = "node2/outputs/p2pn2n3Output.json"
RECEIVED_FILE = "node2/inputs/p2pn2n3Input.json"

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
                    print("Sent node2 data:", data)
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
            print("Received node3's data:", data)
        except Exception as e:
            print("Receive error:", e)

async def main():
    uri = f"ws://{NODE3_IP}:{PORT}"
    print("Connecting to node3 on 8766...")
    async with websockets.connect(uri) as websocket:
        print("Connected to node3!")
        await asyncio.gather(
            send_my_file(websocket),
            receive_data(websocket)
        )

if __name__ == "__main__":
    asyncio.run(main())
