import cv2
import numpy as np


# ---------------- ARUCO SETUP ---------------- #

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

aruco_params = cv2.aruco.DetectorParameters()

aruco_detector = cv2.aruco.ArucoDetector(
    aruco_dict,
    aruco_params
)


# ---------------- COLOR DETECTION ---------------- #

def detect_bin_color(frame):

    h, w = frame.shape[:2]

    # Center ROI only
    roi = frame[
        int(h * 0.2):int(h * 0.8),
        int(w * 0.2):int(w * 0.8)
    ]

    # Blur reduces camera noise
    blurred = cv2.GaussianBlur(roi, (5, 5), 0)

    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # =========================================================
    # GREEN = WET
    # =========================================================

    lower_green = np.array([40, 80, 50])
    upper_green = np.array([85, 255, 255])

    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # =========================================================
    # BLUE = DRY
    # =========================================================

    lower_blue = np.array([100, 120, 50])
    upper_blue = np.array([130, 255, 255])

    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # =========================================================
    # MORPHOLOGICAL FILTERING
    # =========================================================

    kernel = np.ones((5, 5), np.uint8)

    mask_green = cv2.morphologyEx(
        mask_green,
        cv2.MORPH_OPEN,
        kernel
    )

    mask_green = cv2.morphologyEx(
        mask_green,
        cv2.MORPH_CLOSE,
        kernel
    )

    mask_blue = cv2.morphologyEx(
        mask_blue,
        cv2.MORPH_OPEN,
        kernel
    )

    mask_blue = cv2.morphologyEx(
        mask_blue,
        cv2.MORPH_CLOSE,
        kernel
    )

    # =========================================================
    # CONTOUR DETECTION
    # =========================================================

    contours_green, _ = cv2.findContours(
        mask_green,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours_blue, _ = cv2.findContours(
        mask_blue,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # ---------------------------------------------------------
    # GREEN CHECK
    # ---------------------------------------------------------

    for cnt in contours_green:

        area = cv2.contourArea(cnt)

        if area > 5000:

            hull = cv2.convexHull(cnt)

            hull_area = cv2.contourArea(hull)

            if hull_area == 0:
                continue

            solidity = float(area) / hull_area

            if solidity > 0.7:

                return "WET"

    # ---------------------------------------------------------
    # BLUE CHECK
    # ---------------------------------------------------------

    for cnt in contours_blue:

        area = cv2.contourArea(cnt)

        if area > 5000:

            hull = cv2.convexHull(cnt)

            hull_area = cv2.contourArea(hull)

            if hull_area == 0:
                continue

            solidity = float(area) / hull_area

            if solidity > 0.7:

                return "DRY"

    return None


# ---------------- ARUCO DETECTION ---------------- #

def detect_aruco(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, _ = aruco_detector.detectMarkers(gray)

    if ids is not None:

        cv2.aruco.drawDetectedMarkers(
            frame,
            corners,
            ids
        )

        for marker_id in ids.flatten():

            # DRY BIN
            if marker_id == 0:
                return "DRY"

            # WET BIN
            if marker_id == 1:
                return "WET"

    return None


# ---------------- FINAL BIN DECISION ---------------- #

def detect_bin(frame):

    # =========================================================
    # 1. ARUCO FIRST (MOST RELIABLE)
    # =========================================================

    aruco_result = detect_aruco(frame)

    if aruco_result is not None:
        return aruco_result

    # =========================================================
    # 2. COLOR FALLBACK
    # =========================================================

    color_result = detect_bin_color(frame)

    if color_result is not None:
        return color_result

    # =========================================================
    # 3. NOTHING DETECTED
    # =========================================================

    return None