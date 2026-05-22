import cv2
import numpy as np


# ================= RIGHT LANE DETECTION ================= #

def detect_right_lane(frame):

    h, w = frame.shape[:2]

    # Only bottom 40% of frame
    roi = frame[int(h*0.6):h, :]

    # Convert to HSV for white detection
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 50, 255])

    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Remove noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, frame

    # Select largest white contour
    largest = max(contours, key=cv2.contourArea)

    area = cv2.contourArea(largest)

    if area < 1500:
        return None, frame

    M = cv2.moments(largest)

    if M["m00"] == 0:
        return None, frame

    cx = int(M["m10"] / M["m00"])

    # Convert back to global coordinates
    cx_global = cx
    target_x = int(w * 0.75)

    # Draw debug lines
    cv2.line(frame, (cx_global, int(h*0.6)), (cx_global, h), (255, 0, 0), 3)
    cv2.line(frame, (target_x, 0), (target_x, h), (0, 255, 0), 2)

    error = cx_global - target_x

    return error, frame


# ================= HORIZONTAL MARKER ================= #

def detect_horizontal_marker(frame):

    h, w = frame.shape[:2]

    # Only middle lower region
    roi = frame[int(h*0.45):int(h*0.65), :]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 50, 255])

    mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area < 4000:
            continue

        x, y, cw, ch = cv2.boundingRect(cnt)

        aspect_ratio = cw / float(ch)

        # Horizontal strip condition
        if aspect_ratio > 5 and cw > w * 0.6:
            return True, frame

    return False, frame