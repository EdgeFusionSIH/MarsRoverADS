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
    if model_tier == "medium":
        model_name = "yolov8m-world.pt"
        print("Model Tier: MEDIUM (yolov8m-world.pt) - Prioritizing Accuracy")
    else:
        model_name = "yolov8s-world.pt"
        print("Model Tier: LIGHT (yolov8s-world.pt) - Prioritizing Speed")

    model = YOLO(model_name)
    
    # Expanded prompt set to force matches on Martian surface structures
    custom_classes = ["rock", "boulder", "stone", "obstacle", "large object", "protrusion"]
    model.set_classes(custom_classes)
    
    print(f"Zero-Shot targets locked: {custom_classes}")
    return model


def run_detection(model, image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image file.")
        return None

    # --- ADVANCED MARS EDGE & CONTRAST ENHANCEMENT ---
    # Converts to LAB color space to separate color from structural lighting shadows
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply aggressive local contrast equalization to make the rock shadow pop
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
    cl = clahe.apply(l)
    
    enhanced_lab = cv2.merge((cl, a, b))
    processed_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    # ------------------------------------------------

    # Ultra-low confidence threshold + low IoU to prevent suppression
    results = model(processed_img, conf=0.01, iou=0.2)
    
    detections = []
    img_with_boxes = img.copy()  # Clean raw image for the UI display
    
    for r in results:
        for box in r.boxes:
            conf = round(float(box.conf[0]), 2)
            cls = int(box.cls[0])
            name = model.names[cls]
            detections.append({"object": name, "confidence": conf})
            
            # Draw explicit bounding boxes on the output frame
            b_coords = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(b_coords[0]), int(b_coords[1]), int(b_coords[2]), int(b_coords[3])
            cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img_with_boxes, f"{name} {conf}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
    # Handle Image Backups for Node 3 Streamer
    if os.path.exists(CURRENT_FRAME):
        shutil.move(CURRENT_FRAME, LAST_FRAME)
        
    cv2.imwrite(CURRENT_FRAME, img_with_boxes)
    
    return detections


def generate_outputs(detections):
    # Gather System Hardware Telemetry safely
    raw_sys = sysUs.get_system_info()
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
        
    # Format Top 3 Objects (Padding with "nill" and 0.0 if fewer than 3 are detected)
    sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    top_3 = sorted_dets[:3]
    
    objects_dict = {}
    
    for i in range(1, 4):
        if i <= len(top_3):
            objects_dict[f"obj{i}"] = top_3[i-1]["object"]
            objects_dict[f"conf{i}"] = top_3[i-1]["confidence"]
        else:
            objects_dict[f"obj{i}"] = "nill"
            objects_dict[f"conf{i}"] = 0.0

    # Construct Final Output Payload matching Node 2 schema exactly[cite: 1]
    output_json = {
        "from": "node1",
        "to": "node2",
        "sysus": sysus_dict,
        "objects": objects_dict
    }
    
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output_json, f, indent=4)
        
    return output_json


def main():
    print("========================================")
    print("  NODE 1 VISION: ENHANCED MARS PIPELINE")
    print("========================================")

    input_data = read_input_json()
    if not input_data:
        return

    img_num = input_data.get("img")
    req_model = input_data.get("model", "light").lower()

    if not img_num:
        print("Invalid input JSON: Missing 'img'.")
        return

    image_path = find_image(img_num)
    if not image_path:
        return
        
    model = load_rover_model(req_model)
    detections = run_detection(model, image_path)
    if detections is None:
        return

    final_output = generate_outputs(detections)
    
    print("\n[SUCCESS] Pipeline Completed.")
    print(f"Data saved to {OUTPUT_JSON}:\n")
    print(json.dumps(final_output, indent=2))


if __name__ == "__main__":
    main()