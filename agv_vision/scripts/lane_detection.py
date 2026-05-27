import cv2
import numpy as np


# ================= RIGHT LANE DETECTION ================= #

def detect_right_lane(frame):

    h, w = frame.shape[:2]

    # Bottom ROI
    roi_top = int(h * 0.6)
    roi = frame[roi_top:h, :]

    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # White color range
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 50, 255])

    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Noise removal
    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None, frame

    # Largest contour
    largest = max(contours, key=cv2.contourArea)

    area = cv2.contourArea(largest)

    if area < 1500:
        return None, frame

    # ================= DRAW FULL BLUE LANE ================= #

    # Shift contour to original frame coordinates
    largest_global = largest.copy()
    largest_global[:, :, 1] += roi_top

    # Draw detected lane contour in BLUE
    cv2.drawContours(
        frame,
        [largest_global],
        -1,
        (255, 0, 0),
        3
    )

    # ================= CENTER CALCULATION ================= #

    M = cv2.moments(largest)

    if M["m00"] == 0:
        return None, frame

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # Convert ROI coordinates to frame coordinates
    cx_global = cx
    cy_global = cy + roi_top

    # Reference position
    target_x = int(w * 0.75)

    # Draw center point
    cv2.circle(
        frame,
        (cx_global, cy_global),
        6,
        (0, 255, 255),
        -1
    )

    # Draw target line
    cv2.line(
        frame,
        (target_x, 0),
        (target_x, h),
        (0, 255, 0),
        2
    )

    # Draw line from lane center to target
    cv2.line(
        frame,
        (cx_global, cy_global),
        (target_x, cy_global),
        (0, 0, 255),
        2
    )

    # Steering error
    error = cx_global - target_x

    # Display error value
    cv2.putText(
        frame,
        f"Error: {error}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    return error, frame


# ================= HORIZONTAL MARKER ================= #

def detect_horizontal_marker(frame):

    h, w = frame.shape[:2]

    # ROI for horizontal line detection
    roi_top = int(h * 0.45)
    roi_bottom = int(h * 0.65)

    roi = frame[roi_top:roi_bottom, :]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 50, 255])

    mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area < 4000:
            continue

        x, y, cw, ch = cv2.boundingRect(cnt)

        aspect_ratio = cw / float(ch)

        # Horizontal strip condition
        if aspect_ratio > 5 and cw > w * 0.6:

            # Convert contour to frame coordinates
            cnt_global = cnt.copy()
            cnt_global[:, :, 1] += roi_top

            # Draw detected horizontal marker in RED
            cv2.drawContours(
                frame,
                [cnt_global],
                -1,
                (0, 0, 255),
                4
            )

            cv2.putText(
                frame,
                "HORIZONTAL MARKER",
                (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

            return True, frame

    return False, frame
