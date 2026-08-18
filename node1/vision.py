import json
import os
import shutil
import cv2
import psutil
from PIL import Image

# The magic library that runs Google's Zero-Shot AI
from transformers import pipeline 

# Import your system usage module
import sysUs

# ============================================================
# PATHS
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

INPUT_JSON = os.path.join(INPUT_DIR, "p2pn1n2Input.json")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "p2pn1n2Output.json")
CURRENT_FRAME = os.path.join(OUTPUT_DIR, "currentFrame.jpg")
LAST_FRAME = os.path.join(OUTPUT_DIR, "lastFrame.jpg")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)


def read_input_json():
    if not os.path.exists(INPUT_JSON): return None
    with open(INPUT_JSON, "r") as f: return json.load(f)


def find_image(image_number):
    img_path = os.path.join(DATASET_DIR, f"img{image_number}.jpg")
    return img_path if os.path.exists(img_path) else None


def load_rover_model():
    print("Loading Google OWL-ViT (Zero-Shot Space AI)...")
    # This downloads the model to your cache once, then runs 100% offline.
    # No 'git' or 'clip' dependencies required.
    detector = pipeline(
        task="zero-shot-object-detection",
        model="google/owlvit-base-patch32"
    )
    return detector


def run_detection(detector, image_path, model_tier):
    img_cv = cv2.imread(image_path)
    if img_cv is None: return None

    img_pil = Image.open(image_path).convert("RGB")
    
    # --- DYNAMIC TIER SWITCHING ---
    if model_tier == "medium":
        print("--> Configured for MEDIUM: Deep Scan (5 targets, High Sensitivity)")
        mars_targets = ["boulder", "rock", "crater", "crease", "surface crack"]
        conf_threshold = 0.04
    else:
        print("--> Configured for LIGHT: Fast Scan (2 targets, Low Compute)")
        mars_targets = ["boulder", "crater"]
        conf_threshold = 0.08
        
    print(f"Scanning terrain for: {mars_targets}")
    predictions = detector(
        img_pil,
        candidate_labels=mars_targets
    )
    
    detections = []
    img_with_boxes = img_cv.copy()
    
    for pred in predictions:
        conf = round(pred['score'], 2)
        
        # Applies the threshold based on the requested tier
        if conf < conf_threshold: 
            continue
            
        name = pred['label']
        box = pred['box']
        
        detections.append({"object": name, "confidence": conf})
        
        x1, y1, x2, y2 = int(box['xmin']), int(box['ymin']), int(box['xmax']), int(box['ymax'])
        
        cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), (0, 165, 255), 2)
        cv2.putText(img_with_boxes, f"{name} {conf}", (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

    if os.path.exists(CURRENT_FRAME):
        shutil.move(CURRENT_FRAME, LAST_FRAME)
        
    cv2.imwrite(CURRENT_FRAME, img_with_boxes)
    return detections


def generate_outputs(detections):
    raw_sys = sysUs.get_system_info()
    sysus_dict = {
        "nodeid": 1,
        "cpu": raw_sys.get("cpu", raw_sys.get("cpu_usage_percent", 0.0)),
        "gpu": raw_sys.get("gpu", 0.0),
        "ram": raw_sys.get("ram", raw_sys.get("ram_usage_percent", 0.0)),
        "disk": round(psutil.disk_usage('/').percent, 1)
    }
        
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
    print("  NODE 1 VISION: ZERO-SHOT PIPELINE")
    print("========================================")

    print("[DEBUG] Reading input JSON...")
    input_data = read_input_json()
    if not input_data:
        print("[ERROR] read_input_json() returned None or empty!")
        return
    print(f"[DEBUG] Input data loaded: {input_data}")

    img_num = input_data.get("img")
    req_model = input_data.get("model", "light").lower()
    
    if not img_num:
        print("[ERROR] 'img' key missing from input JSON!")
        return

    print(f"[DEBUG] Looking for image number: {img_num}")
    image_path = find_image(img_num)
    if not image_path:
        print(f"[ERROR] find_image() could not locate image for id '{img_num}' in dataset folder!")
        return
    print(f"[DEBUG] Found image at: {image_path}")
        
    print("[DEBUG] Loading OWL-ViT model...")
    detector = load_rover_model()
    
    print("[DEBUG] Running detection...")
    detections = run_detection(detector, image_path, req_model)
    if detections is None:
        print("[ERROR] run_detection() failed or returned None!")
        return
    print(f"[DEBUG] Detections found: {detections}")

    print("[DEBUG] Generating output JSON...")
    final_output = generate_outputs(detections)
    
    print("\n[SUCCESS] Pipeline Completed.")
    print(f"Data saved to {OUTPUT_JSON}:\n")
    print(json.dumps(final_output, indent=2))
    if __name__ == "__main__":
        main()