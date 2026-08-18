import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NODE1_INPUT = os.path.join(BASE_DIR, "inputs", "p2pn1n2Input.json")
NODE2_SYSUS = os.path.join(BASE_DIR, "dataset", "systemInfo.json")
NODE3_OUTPUT = os.path.join(BASE_DIR, "outputs", "p2pn2n3Output.json")

def read_node1_sysus():
    """Reads Node 1 system info received from p2pn1n2Input.json"""
    try:
        if os.path.exists(NODE1_INPUT):
            with open(NODE1_INPUT, "r") as f:
                data = json.load(f)
                return data.get("sysus", {})
    except Exception as e:
        pass
    return {}

def read_node2_sysus():
    """Reads Node 2 system info from dataset/systemInfo.json"""
    try:
        if os.path.exists(NODE2_SYSUS):
            with open(NODE2_SYSUS, "r") as f:
                data = json.load(f)
                return data
    except Exception as e:
        pass
    return {}

def update_broadcast_json():
    """Aggregates both sysus and updates the output json to broadcast to Node 3"""
    node1_info = read_node1_sysus()
    node2_info = read_node2_sysus()

    try:
        if os.path.exists(NODE3_OUTPUT):
            with open(NODE3_OUTPUT, "r") as f:
                output_data = json.load(f)
        else:
            output_data = {}

        # Store as nested dicts. Duplicate keys in same dict break JSON.
        output_data["sysus"] = {
            "node1": node1_info,
            "node2": node2_info
        }

        with open(NODE3_OUTPUT, "w") as f:
            json.dump(output_data, f, indent=4)
        
        print("Updated p2pn2n3Output.json with Node 1 & Node 2 sysus.")

    except Exception as e:
        print(f"Error updating output JSON: {e}")

if __name__ == "__main__":
    print("Starting Node 2 Main sysus aggregator...")
    while True:
        update_broadcast_json()
        time.sleep(1)
