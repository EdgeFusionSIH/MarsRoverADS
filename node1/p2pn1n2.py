import asyncio
import json
import os
import socket
import websockets

WS_PORT = 8765
DISCOVERY_PORT = 9999

MY_FILE = "outputs\\p2pn1n2Output.json"
RECEIVED_FILE = "inputs\\p2pn1n2Input.json"


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

async def discovery_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", DISCOVERY_PORT))

    print(f"Discovery server running on UDP port {DISCOVERY_PORT}")

    loop = asyncio.get_running_loop()

    while True:
        data, address = await loop.sock_recvfrom(sock, 1024)

        if data.decode() == "DISCOVER_BHAVIKA":
            print(f"Discovery request from {address[0]}")

            await loop.sock_sendto(
                sock,
                b"BHAVIKA_SERVER",
                address
            )

async def main():
    print(f"WebSocket server running on port {WS_PORT}")

    async with websockets.serve(
        handler,
        "0.0.0.0",
        WS_PORT
    ):
        await discovery_server()

asyncio.run(main())