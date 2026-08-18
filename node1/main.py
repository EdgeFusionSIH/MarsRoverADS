import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NODE1_SYSUS = os.path.join(BASE_DIR, "dataset", "systemInfo.json")
NODE2_OUTPUT = os.path.join(BASE_DIR, "outputs", "p2pn1n2Output.json")

def read_node1_sysus():
    try:
        if os.path.exists(NODE1_SYSUS):
            with open(NODE1_SYSUS, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def update_broadcast_json():
    node1_info = read_node1_sysus()

    try:
        if os.path.exists(NODE2_OUTPUT):
            with open(NODE2_OUTPUT, "r") as f:
                output_data = json.load(f)
        else:
            output_data = {
                "from": "node1",
                "to": "node2",
                "sysus": {},
                "objects": {}
            }

        if node1_info:
            output_data["sysus"] = node1_info

        with open(NODE2_OUTPUT, "w") as f:
            json.dump(output_data, f, indent=4)
        
        print("Updated p2pn1n2Output.json with Node 1 sysus.")

    except Exception as e:
        print(f"Error updating output JSON: {e}")

if __name__ == "__main__":
    print("Starting Node 1 Main sysus aggregator...")
    while True:
        update_broadcast_json()
        time.sleep(1)
