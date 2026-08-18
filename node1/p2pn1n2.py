import asyncio
import json
import os
import websockets

NODE2_IP = "172.20.10.12"
PORT = 8765

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MY_FILE = os.path.join(BASE_DIR, "outputs", "p2pn1n2Output.json")
RECEIVED_FILE = os.path.join(BASE_DIR, "inputs", "p2pn1n2Input.json")

async def send_my_file(websocket):
    while True:
        try:
            if os.path.exists(MY_FILE):
                with open(MY_FILE, "r") as file:
                    data = json.load(file)
                await websocket.send(json.dumps(data))
                print("Sent node1 data:", data)
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

async def main():
    uri = f"ws://{NODE2_IP}:{PORT}"
    print("Connecting to node2...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to node2!")
            await asyncio.gather(
                send_my_file(websocket),
                receive_data(websocket)
            )
    except Exception as e:
        print(f"Failed to connect to node 2: {e}")

if __name__ == "__main__":
    asyncio.run(main())