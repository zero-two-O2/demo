import cv2
import numpy as np

def detect_bin_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # BLUE → WET
    lower_blue = np.array([90, 80, 50])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # GREEN → DRY
    lower_green = np.array([35, 80, 50])
    upper_green = np.array([85, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    blue_pixels = cv2.countNonZero(mask_blue)
    green_pixels = cv2.countNonZero(mask_green)

    if blue_pixels > 3000 and blue_pixels > green_pixels:
        return "WET"

    if green_pixels > 3000 and green_pixels > blue_pixels:
        return "DRY"

    return None
