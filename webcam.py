import cv2
from ultralytics import YOLO

# load the YOLO medium model
model = YOLO("yolov8m.pt")

print("\nChoose camera source:")
print("1 - Laptop webcam")
print("2 - USB / phone webcam")
print("3 - Phone camera over Wi-Fi")

choice = input("\nEnter your choice: ").strip()


# laptop webcam
if choice == "1":

    camera = cv2.VideoCapture(0)


# USB / phone webcam
elif choice == "2":

    print("\nEnter the camera number.")
    print("Try 1 first. If that doesn't work, try 2, 3, etc.")

    camera_number = input("Camera number: ").strip()

    try:
        camera_number = int(camera_number)
    except ValueError:
        print("Invalid camera number.")
        exit()

    camera = cv2.VideoCapture(camera_number)


# phone camera over Wi-Fi
elif choice == "3":

    stream_url = input("\nEnter your phone camera stream URL: ").strip()

    camera = cv2.VideoCapture(stream_url)


else:

    print("Invalid choice.")
    exit()


# check if the camera opened
if not camera.isOpened():

    print("\nCould not open the selected camera.")
    print("Check that the camera is connected and try again.")
    exit()


print("\nCamera opened successfully!")
print("YOLOv8-Medium is running.")
print("Press Q to stop.\n")


while True:

    # get the next frame from the camera
    success, frame = camera.read()

    if not success:
        print("Could not read camera frame.")
        break

    # run YOLO on the current frame
    results = model(frame, verbose=False)

    # draw the detected objects
    output = results[0].plot()

    # show the processed camera feed
    cv2.imshow("YOLOv8 Medium - Live Detection", output)

    # press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# close the camera and window
camera.release()
cv2.destroyAllWindows()

print("Camera stopped.")