import json
import os
import shutil
import cv2
from ultralytics import YOLO


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

INPUT_JSON = os.path.join(INPUT_DIR, "p2pn1n2Input.json")

CURRENT_FRAME = os.path.join(OUTPUT_DIR, "currentFrame.jpg")
LAST_FRAME = os.path.join(OUTPUT_DIR, "lastFrame.jpg")

MODEL_PATHS = {
    "yolov8m": os.path.join(BASE_DIR, "yolov8m.pt"),
    "yolov8n": os.path.join(BASE_DIR, "yolov8n.pt"),
}


# ============================================================
# PREPARE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# READ INPUT JSON
# ============================================================

def read_input_json():

    if not os.path.exists(INPUT_JSON):
        print(f"Input JSON not found: {INPUT_JSON}")
        return None

    try:
        with open(INPUT_JSON, "r") as file:
            data = json.load(file)

        return data

    except json.JSONDecodeError:
        print("Input JSON is invalid.")
        return None

    except Exception as e:
        print(f"Could not read input JSON: {e}")
        return None


# ============================================================
# FIND IMAGE
# ============================================================

def find_image(image_number):

    # Expected examples:
    # 1       -> img1.jpg
    # 2       -> img2.jpg
    # "1"     -> img1.jpg
    # "img1"  -> img1.jpg

    image_number = str(image_number).strip()

    if image_number.lower().startswith("img"):
        image_name = image_number + ".jpg"
    else:
        image_name = f"img{image_number}.jpg"

    image_path = os.path.join(DATASET_DIR, image_name)

    if not os.path.exists(image_path):

        print(f"Image not found: {image_path}")
        return None

    return image_path


# ============================================================
# LOAD REQUESTED YOLO MODEL
# ============================================================

def load_model(model_name):

    model_name = str(model_name).strip().lower()

    if model_name not in MODEL_PATHS:

        print(f"Unsupported YOLO model: {model_name}")
        print("Available models:")
        print(" - yolov8m")
        print(" - yolov8n")

        return None

    model_path = MODEL_PATHS[model_name]

    if not os.path.exists(model_path):

        print(f"Model file not found: {model_path}")
        return None

    print(f"\nLoading model: {model_name}")
    print(f"Model file: {model_path}")

    try:

        model = YOLO(model_path)

        print("Model loaded successfully.")

        return model

    except Exception as e:

        print(f"Could not load YOLO model: {e}")
        return None


# ============================================================
# RUN YOLO
# ============================================================

def run_detection(model, image_path):

    print(f"\nProcessing image: {image_path}")

    try:

        results = model(image_path, verbose=False)

        result = results[0]

        # Create annotated image in memory
        annotated_frame = result.plot()

        # ----------------------------------------------------
        # Move current frame to last frame
        # ----------------------------------------------------

        if os.path.exists(CURRENT_FRAME):

            shutil.copyfile(
                CURRENT_FRAME,
                LAST_FRAME
            )

        # ----------------------------------------------------
        # Save newly processed frame as current frame
        # ----------------------------------------------------

        success = cv2.imwrite(
            CURRENT_FRAME,
            annotated_frame
        )

        if not success:
            print("Could not save currentFrame.jpg")
            return None

        print(f"Saved: {CURRENT_FRAME}")

        if os.path.exists(LAST_FRAME):
            print(f"Updated: {LAST_FRAME}")

        # ----------------------------------------------------
        # Extract detections
        # ----------------------------------------------------

        detections = []

        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                class_name = result.names[class_id]

                detections.append({
                    "object": class_name,
                    "confidence": round(confidence * 100, 2)
                })

        return detections

    except Exception as e:

        print(f"YOLO detection failed: {e}")
        return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n==========================================")
    print("              NODE 1 VISION")
    print("==========================================")

    # --------------------------------------------------------
    # Read JSON
    # --------------------------------------------------------

    input_data = read_input_json()

    if input_data is None:
        return

    print("\nInput JSON received:")
    print(input_data)

    # --------------------------------------------------------
    # Get image + model
    # --------------------------------------------------------

    image_number = input_data.get("image")
    model_name = input_data.get("model")

    if image_number is None:
        print("Input JSON is missing 'image'.")
        return

    if model_name is None:
        print("Input JSON is missing 'model'.")
        return

    # --------------------------------------------------------
    # Find requested image
    # --------------------------------------------------------

    image_path = find_image(image_number)

    if image_path is None:
        return

    # --------------------------------------------------------
    # Load requested model
    # --------------------------------------------------------

    model = load_model(model_name)

    if model is None:
        return

    # --------------------------------------------------------
    # Run detection
    # --------------------------------------------------------

    detections = run_detection(
        model,
        image_path
    )

    if detections is None:
        return

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\nDetection results:")

    if len(detections) == 0:

        print("No objects detected.")

    else:

        for detection in detections:

            print(
                f"- {detection['object']} "
                f"({detection['confidence']}%)"
            )

    print("\nVision processing complete.")


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()