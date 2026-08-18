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

MODEL_PATHS = {
    "yolov8m": os.path.join(BASE_DIR, "yolov8m.pt"),
    "yolov8n": os.path.join(BASE_DIR, "yolov8n.pt"),
}

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


def load_model(model_name):
    path = MODEL_PATHS.get(model_name)
    if not path or not os.path.exists(path):
        print(f"Model file not found: {path}")
        return None
    return YOLO(path)


def run_detection(model, image_path):
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image file. (Check if it is 0 bytes or corrupted).")
        return None

    # Run inference
    results = model(img)
    
    detections = []
    
    for r in results:
        # Draw bounding boxes on the image
        img_with_boxes = r.plot()
        
        # Extract object names and confidences
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
    raw_sys = sysUs.get_system_usage()
    
    # Extract first GPU usage safely
    gpu_val = 0.0
    if raw_sys.get("gpu") and len(raw_sys["gpu"]) > 0:
        gpu_val = raw_sys["gpu"][0]["usage_percent"]
        
    # Get Disk usage (Not in sysUs.py, required by JSON format)
    disk_val = round(psutil.disk_usage('/').percent, 1)

    sysus_dict = {
        "nodeid": 1,
        "cpu": raw_sys["cpu_usage_percent"],
        "gpu": gpu_val,
        "ram": raw_sys["ram_usage_percent"],
        "disk": disk_val
    }

    # 2. Write systemInfo.json to dataset folder
    with open(SYS_INFO_JSON, "w") as f:
        json.dump(sysus_dict, f, indent=4)
        
    # 3. Format Top 3 Objects
    # Sort by confidence descending
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
    print("       NODE 1 VISION & TELEMETRY")
    print("========================================")

    # 1. Read input
    input_data = read_input_json()
    if not input_data:
        return

    img_num = input_data.get("img")
    req_model = input_data.get("model")

    if not img_num or not req_model:
        print("Invalid input JSON: Missing 'img' or 'model'.")
        return

    # Translate "light"/"medium" to file names
    if req_model == "light":
        model_name = "yolov8n"
    elif req_model == "medium":
        model_name = "yolov8m"
    else:
        model_name = "yolov8n" # Default

    # 2. Find Image & Load Model
    image_path = find_image(img_num)
    model = load_model(model_name)
    if not image_path or not model:
        return

    # 3. Run YOLO
    detections = run_detection(model, image_path)
    if detections is None:
        return

    # 4. Generate JSON Outputs
    final_output = generate_outputs(detections)
    
    print("\n[SUCCESS] Pipeline Completed.")
    print(f"Data saved to {OUTPUT_JSON}:\n")
    print(json.dumps(final_output, indent=2))


if __name__ == "__main__":
    main()