import asyncio
import json
import os
import websockets

NODE3_IP = "172.20.10.12" # library test aug 18 10:10 PM hostel wifi
PORT = 8767

MY_FILE = "node1/outputs/p2pn1n3Output.json"
RECEIVED_FILE = "node1/inputs/p2pn1n3Input.json"
IMAGE_FILE = "node1/dataset/lastFrame.jpg"

async def send_my_file(websocket):
    last_modified = 0
    last_img_modified = 0

    while True:
        try:
            # Send JSON
            if os.path.exists(MY_FILE):
                modified = os.path.getmtime(MY_FILE)
                if modified != last_modified:
                    last_modified = modified
                    with open(MY_FILE, "r") as file:
                        data = json.load(file)
                    await websocket.send(json.dumps(data))
                    print("Sent node1 data:", data)
            
            # Send Image
            if os.path.exists(IMAGE_FILE):
                img_modified = os.path.getmtime(IMAGE_FILE)
                if img_modified != last_img_modified:
                    last_img_modified = img_modified
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
    async with websockets.connect(uri) as websocket:
        print("Connected to node3!")
        await asyncio.gather(
            send_my_file(websocket),
            receive_data(websocket)
        )

if __name__ == "__main__":
    asyncio.run(main())
