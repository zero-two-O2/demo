import cv2
import numpy as np


# ---------------- ARUCO SETUP ---------------- #

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters()
aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)


# ---------------- COLOR DETECTION (ROBUST VERSION) ---------------- #

def detect_bin_color(frame):

    h, w = frame.shape[:2]

    # Only check center area (ignore background edges)
    roi = frame[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # -------- RED (WET) -------- #
    lower_red1 = np.array([0, 120, 100])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 120, 100])
    upper_red2 = np.array([180, 255, 255])

    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + \
               cv2.inRange(hsv, lower_red2, upper_red2)

    # -------- YELLOW (DRY) -------- #
    lower_yellow = np.array([20, 120, 120])
    upper_yellow = np.array([35, 255, 255])

    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Remove noise
    kernel = np.ones((5, 5), np.uint8)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)

    # Contour detection
    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours_red:
        area = cv2.contourArea(cnt)
        if area > 5000:  # Large enough blob
            return "WET"

    for cnt in contours_yellow:
        area = cv2.contourArea(cnt)
        if area > 5000:
            return "DRY"

    return None


# ---------------- ARUCO DETECTION ---------------- #

def detect_aruco(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, _ = aruco_detector.detectMarkers(gray)

    if ids is not None:

        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for marker_id in ids.flatten():

            if marker_id == 0:
                return "DRY"

            if marker_id == 1:
                return "WET"

    return None


# ---------------- FINAL BIN DECISION ---------------- #

def detect_bin(frame):

    # ARUCO FIRST (Most Reliable)
    aruco_result = detect_aruco(frame)
    if aruco_result:
        return aruco_result

    # COLOR FALLBACK
    color_result = detect_bin_color(frame)
    if color_result:
        return color_result

    return None