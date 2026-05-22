from picamera2 import Picamera2
import cv2
import numpy as np
import time

# ===============================
# CAMERA INITIALIZATION
# ===============================

# Camera 1 → Navigation
cam1 = Picamera2(0)
cam1.configure(cam1.create_preview_configuration(main={"size": (640,480)}))
cam1.start()

# Camera 2 → Bin Detection
cam2 = Picamera2(1)
cam2.configure(cam2.create_preview_configuration(main={"size": (640,480)}))
cam2.start()

time.sleep(2)

# ===============================
# LANE DETECTION FUNCTION (C1)
# ===============================

def detect_lane(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 50, 150)

    height, width = edges.shape

    # Region of Interest (bottom half)
    roi = edges[int(height*0.6):height, :]

    lines = cv2.HoughLinesP(
        roi,
        1,
        np.pi/180,
        50,
        minLineLength=50,
        maxLineGap=20
    )

    if lines is not None:
        return True
    else:
        return False


# ===============================
# OBSTACLE DETECTION FUNCTION (C1)
# ===============================

def detect_obstacle(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area > 8000:
            return True

    return False


# ===============================
# BIN COLOR DETECTION FUNCTION (C2)
# ===============================

def detect_bin_color(frame):

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    colors = {
        "green": ((35,80,50), (85,255,255)),
        "blue":  ((90,80,50), (130,255,255)),
        "red":   ((0,100,50), (10,255,255))
    }

    for color_name, (lower, upper) in colors.items():

        mask = cv2.inRange(hsv, lower, upper)
        area = cv2.countNonZero(mask)

        if area > 7000:
            return color_name

    return None


# ===============================
# MAIN LOOP
# ===============================

while True:

    # Capture frames
    frame1 = cam1.capture_array()
    frame2 = cam2.capture_array()

    # -------- C1 PROCESSING --------
    lane = detect_lane(frame1)
    obstacle = detect_obstacle(frame1)

    # -------- C2 PROCESSING --------
    bin_color = detect_bin_color(frame2)

    # ===============================
    # DECISION LOGIC
    # ===============================

    if obstacle:
        print("🚨 STOP - Obstacle Detected")

    elif bin_color:
        print("🗑️ Bin Detected:", bin_color)
        print("➡ Activate Lift Mechanism")

    elif lane:
        print("🚗 Following Lane")

    else:
        print("Searching...")

    # Display for debugging
    cv2.imshow("Camera 1 - Navigation", frame1)
    cv2.imshow("Camera 2 - Bin Detection", frame2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cv2.destroyAllWindows()
