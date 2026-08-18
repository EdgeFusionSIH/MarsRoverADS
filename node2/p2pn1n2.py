import asyncio
import json
import os
import socket
import websockets

WS_PORT = 8765
DISCOVERY_PORT = 9999

MY_FILE = "outputs/p2pn1n2Output.json"
RECEIVED_FILE = "inputs/p2pn1n2Input.json"


async def discover_bhavika():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    sock.settimeout(2)

    message = b"DISCOVER_BHAVIKA"

    # Broadcast to the local network
    sock.sendto(
        message,
        ("255.255.255.255", DISCOVERY_PORT)
    )

    print("Searching for Bhavika...")

    loop = asyncio.get_running_loop()

    while True:
        try:
            data, address = await loop.run_in_executor(
                None,
                sock.recvfrom,
                1024
            )

            if data.decode() == "BHAVIKA_SERVER":
                bhavika_ip = address[0]

                print(f"Bhavika found at {bhavika_ip}")

                sock.close()

                return bhavika_ip

        except socket.timeout:
            print("Bhavika not found.")
            sock.close()
            return None

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

    bhavika_ip = await discover_bhavika()

    if bhavika_ip is None:
        return

    uri = f"ws://{bhavika_ip}:{WS_PORT}"

    print(f"Connecting to Bhavika at {uri}...")

    async with websockets.connect(uri) as websocket:

        print("Connected to Bhavika!")

        await asyncio.gather(
            send_my_file(websocket),
            receive_data(websocket)
        )

asyncio.run(main())