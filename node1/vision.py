import json
import os
import shutil
import traceback
import cv2
import torch
import psutil
from PIL import Image
from transformers import pipeline

# ============================================================
# SAFE TELEMETRY IMPORT
# ============================================================
try:
    import sysUs
    SYSUS_AVAILABLE = True
except ImportError:
    SYSUS_AVAILABLE = False
    print("[SYSTEM] Warning: sysUs.py not found or broken. Using default telemetry values.")

# ============================================================
# DIRECTORY SETUP (Bulletproof Paths)
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

# ============================================================
# CORE FUNCTIONS
# ============================================================
def get_device():
    """Detects your RTX 5050 to force GPU acceleration."""
    if torch.cuda.is_available():
        print(f"[SYSTEM] Hardware Acceleration Enabled: {torch.cuda.get_device_name(0)}")
        return 0 
    else:
        print("[SYSTEM] Warning: CUDA not found, falling back to CPU.")
        return -1

def load_ai_model():
    """Loads Google's Zero-Shot Vision Transformer."""
    print("[AI] Loading OWL-ViT (Zero-Shot Space Vision)...")
    return pipeline(
        task="zero-shot-object-detection",
        model="google/owlvit-base-patch32",
        device=get_device()
    )

def run_vision_scan(detector, image_path, tier):
    """Scans the image based on the JSON tier requirements."""
    print(f"\n[VISION] Processing image: {image_path}")
    
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        raise ValueError(f"OpenCV could not read the image at {image_path}. File might be corrupted.")
    
    img_pil = Image.open(image_path).convert("RGB")
    
    # ---------------------------------------------------------
    # TIER SYSTEM: Changes targets and strictness based on JSON
    # ---------------------------------------------------------
    if tier == "medium":
        print("[VISION] Tier: MEDIUM -> Deep Scan (High GPU usage)")
        targets = ["boulder", "rock", "crater", "surface crack", "sand dune", "crevasse"]
        threshold = 0.05
    else:
        print("[VISION] Tier: LIGHT -> Fast Scan (Low GPU usage)")
        targets = ["boulder", "crater", "rock"]
        threshold = 0.08

    print(f"[VISION] Hunting for: {targets}")
    
    predictions = detector(img_pil, candidate_labels=targets)
    raw_detections = []
    
    for pred in predictions:
        conf = pred['score']
        if conf >= threshold:
            raw_detections.append({
                "object": pred['label'],
                "confidence": round(conf, 2),
                "box": pred['box']
            })
            
    # SORT AND EXTRACT STRICTLY TOP 3
    raw_detections = sorted(raw_detections, key=lambda x: x['confidence'], reverse=True)
    top_3 = raw_detections[:3]
    
    # Draw boxes
    img_with_boxes = img_cv.copy()
    for det in top_3:
        box = det['box']
        name = det['object']
        conf = det['confidence']
        
        x1, y1, x2, y2 = int(box['xmin']), int(box['ymin']), int(box['xmax']), int(box['ymax'])
        cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), (0, 165, 255), 2)
        cv2.putText(img_with_boxes, f"{name} {conf}", (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    # Output management
    if os.path.exists(CURRENT_FRAME):
        shutil.move(CURRENT_FRAME, LAST_FRAME)
    cv2.imwrite(CURRENT_FRAME, img_with_boxes)
    
    return top_3

def generate_output_payload(top_3):
    """Builds the JSON payload for Node 2."""
    print("\n[SYSTEM] Gathering Telemetry & Building JSON...")
    
    cpu_val = gpu_val = ram_val = 0.0
    
    # Safely pull from custom telemetry script if it exists
    if SYSUS_AVAILABLE:
        try:
            raw_sys = sysUs.get_system_info()
            cpu_val = raw_sys.get("cpu", raw_sys.get("cpu_usage_percent", 0.0))
            gpu_val = raw_sys.get("gpu", 0.0)
            ram_val = raw_sys.get("ram", raw_sys.get("ram_usage_percent", 0.0))
        except Exception as e:
            print(f"[SYSTEM] Warning: sysUs telemetry execution failed ({e}).")

    # Fixed the disk pathing issue for Windows compatibility 
    drive_path = os.path.abspath(os.sep)
    sysus_dict = {
        "nodeid": 1,
        "cpu": cpu_val,
        "gpu": gpu_val,
        "ram": ram_val,
        "disk": round(psutil.disk_usage(drive_path).percent, 1)
    }
    
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

# ============================================================
# MAIN EXECUTION ROUTINE
# ============================================================
def main():
    print("========================================")
    print("  NODE 1 VISION: MARTIAN SURFACE PIPELINE")
    print("========================================")

    try:
        # 1. Read JSON safely
        if not os.path.exists(INPUT_JSON):
            raise FileNotFoundError(f"Missing input JSON at {INPUT_JSON}")
            
        with open(INPUT_JSON, "r") as f:
            input_data = json.load(f)
            
        img_num = input_data.get("img")
        tier = input_data.get("model", "light").lower()
        
        if not img_num:
            raise ValueError("Input JSON is missing the 'img' key.")

        # 2. Locate Image (Dynamic extension handling)
        possible_files = [f for f in os.listdir(DATASET_DIR) if f.startswith(f"img{img_num}.")]
        if not possible_files:
            raise FileNotFoundError(f"Could not find any image named 'img{img_num}' in {DATASET_DIR}")
        
        image_path = os.path.join(DATASET_DIR, possible_files[0])

        # 3. Process
        detector = load_ai_model()
        top_3 = run_vision_scan(detector, image_path, tier)
        
        # 4. Output
        final_payload = generate_output_payload(top_3)
        
        print("\n[SUCCESS] Pipeline Completed.")
        print(f"[SUCCESS] Check {CURRENT_FRAME} for visual output.")
        print(f"Data saved to {OUTPUT_JSON}:\n")
        print(json.dumps(final_payload, indent=2))

    except Exception as e:
        print("\n[CRITICAL ERROR] The pipeline crashed!")
        print("Here is the exact reason why:")
        traceback.print_exc()

if __name__ == "__main__":
    main()