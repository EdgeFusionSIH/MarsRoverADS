import asyncio
import json
import os
import websockets

PORT = 8766

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IPS_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "ips.json"))

with open(IPS_FILE, "r") as f:
    ips = json.load(f)
NODE3_IP = ips.get("node3", "127.0.0.1")

MY_FILE = os.path.join(BASE_DIR, "outputs", "p2pn2n3Output.json")
RECEIVED_FILE = os.path.join(BASE_DIR, "inputs", "p2pn2n3Input.json")

async def send_my_file(websocket):
    while True:
        try:
            if os.path.exists(MY_FILE):
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
    print(f"Connecting to node3 at {NODE3_IP} on 8766...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to node3!")
            await asyncio.gather(
                send_my_file(websocket),
                receive_data(websocket)
            )
    except Exception as e:
        print(f"Failed to connect to node 3: {e}")

if __name__ == "__main__":
    asyncio.run(main())
