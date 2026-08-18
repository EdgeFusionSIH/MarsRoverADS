import asyncio
import json
import os
import websockets

NODE3_IP = "172.20.10.13" # Change to actual Node 3 IP
PORT = 8767

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MY_FILE = os.path.join(BASE_DIR, "outputs", "p2pn1n3Output.json")
RECEIVED_FILE = os.path.join(BASE_DIR, "inputs", "p2pn1n3Input.json")
IMAGE_FILE = os.path.join(BASE_DIR, "dataset", "lastFrame.jpg")

async def send_my_file(websocket):
    while True:
        try:
            if os.path.exists(MY_FILE):
                with open(MY_FILE, "r") as file:
                    data = json.load(file)
                await websocket.send(json.dumps(data))
                print("Sent node1 data:", data)
            
            if os.path.exists(IMAGE_FILE):
                with open(IMAGE_FILE, "rb") as f:
                    img_data = f.read()
                await websocket.send(img_data)
                print("Sent lastFrame.jpg")
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
        except json.JSONDecodeError:
            print("Received non-JSON data from Node 3")
        except Exception as e:
            print("Receive error:", e)

async def main():
    uri = f"ws://{NODE3_IP}:{PORT}"
    print("Connecting to node3 on 8767...")
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
