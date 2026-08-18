import json
import os
import shutil
import cv2
import psutil
from ultralytics import YOLO

# Import your system usage module
import sysUs

# ============================================================
# PATHS
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# JSON Paths
INPUT_JSON = os.path.join(INPUT_DIR, "p2pn1n2Input.json")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "p2pn1n2Output.json")
SYS_INFO_JSON = os.path.join(DATASET_DIR, "systemInfo.json")

# Image Paths
CURRENT_FRAME = os.path.join(OUTPUT_DIR, "currentFrame.jpg")
LAST_FRAME = os.path.join(OUTPUT_DIR, "lastFrame.jpg")

# ============================================================
# INITIALIZATION
# ============================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)


def read_input_json():
    if not os.path.exists(INPUT_JSON):
        print(f"Input JSON not found at {INPUT_JSON}")
        return None
    with open(INPUT_JSON, "r") as f:
        return json.load(f)


def find_image(image_number):
    img_name = f"img{image_number}.jpg"
    img_path = os.path.join(DATASET_DIR, img_name)
    if not os.path.exists(img_path):
        print(f"Image not found at {img_path}")
        return None
    return img_path


def load_rover_model(model_tier):
    """
    Loads YOLO-World dynamically based on the requested tier.
    Both fit easily within an 8GB VRAM GPU.
    """
    # 1. Map the JSON request to the specific YOLO-World weights
    if model_tier == "medium":
        model_name = "yolov8m-world.pt"
        print("Model Tier: MEDIUM (yolov8m-world.pt) - Prioritizing Accuracy")
    else:
        # Default to light
        model_name = "yolov8s-world.pt"
        print("Model Tier: LIGHT (yolov8s-world.pt) - Prioritizing Speed")

    # 2. Load the model (Ultralytics will auto-download it on the first run)
    model = YOLO(model_name)
    
    # 3. Inject the zero-shot Martian anomaly classes
    custom_classes = ["rock", "boulder", "crater", "obstacle"]
    model.set_classes(custom_classes)
    
    print(f"Zero-Shot targets locked: {custom_classes}")
    return model


def run_detection(model, image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image file.")
        return None

    # Run inference with a lower confidence threshold for zero-shot text matching
    results = model(img, conf=0.15)
    
    detections = []
    
    for r in results:
        img_with_boxes = r.plot()
        
        for box in r.boxes:
            conf = float(box.conf[0]) * 100
            cls = int(box.cls[0])
            name = model.names[cls]
            detections.append({"object": name, "confidence": round(conf, 1)})
            
    # Handle Image Backups for Node 3 Streamer
    if os.path.exists(CURRENT_FRAME):
        shutil.move(CURRENT_FRAME, LAST_FRAME)
        
    cv2.imwrite(CURRENT_FRAME, img_with_boxes)
    
    return detections


def generate_outputs(detections):
    # 1. Gather System Hardware Telemetry
    raw_sys = sysUs.get_system_info()
    
    # Safely grab the numbers. If a key isn't found, it defaults to 0.0 so it never crashes.
    cpu_val = raw_sys.get("cpu", raw_sys.get("cpu_usage_percent", 0.0))
    gpu_val = raw_sys.get("gpu", 0.0)
    ram_val = raw_sys.get("ram", raw_sys.get("ram_usage_percent", 0.0))
    disk_val = round(psutil.disk_usage('/').percent, 1)

    sysus_dict = {
        "nodeid": 1,
        "cpu": cpu_val,
        "gpu": gpu_val,
        "ram": ram_val,
        "disk": disk_val
    }

    # 2. Write systemInfo.json
    with open(SYS_INFO_JSON, "w") as f:
        json.dump(sysus_dict, f, indent=4)
        
    # 3. Format Top 3 Objects
    sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    top_3 = sorted_dets[:3]
    
    objects_dict = {}
    for i, det in enumerate(top_3, start=1):
        objects_dict[f"obj{i}"] = det["object"]
        objects_dict[f"conf{i}"] = det["confidence"]

    # 4. Construct Final Output Payload
    output_json = {
        "from": "node1",
        "to": "node2",
        "sysus": sysus_dict,
        "objects": objects_dict
    }
    
    # Write p2pn1n2Output.json
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output_json, f, indent=4)
        
    return output_json


def main():
    print("========================================")
    print("  NODE 1 VISION: DYNAMIC ZERO-SHOT AI")
    print("========================================")

    # 1. Read input payload
    input_data = read_input_json()
    if not input_data:
        return

    img_num = input_data.get("img")
    req_model = input_data.get("model", "light").lower()

    if not img_num:
        print("Invalid input JSON: Missing 'img'.")
        return

    # 2. Find image
    image_path = find_image(img_num)
    if not image_path:
        return
        
    # 3. Load the specific model requested by Node 2
    model = load_rover_model(req_model)

    # 4. Process frame and save telemetry
    detections = run_detection(model, image_path)
    if detections is None:
        return

    final_output = generate_outputs(detections)
    
    print("\n[SUCCESS] Pipeline Completed.")
    print(f"Data saved to {OUTPUT_JSON}:\n")
    print(json.dumps(final_output, indent=2))


if __name__ == "__main__":
    main()