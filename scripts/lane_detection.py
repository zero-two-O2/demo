import cv2
import numpy as np


# ================= RIGHT LANE DETECTION ================= #

def detect_right_lane(frame):

    h, w = frame.shape[:2]

    # Bottom 40% ROI only
    roi_top = int(h * 0.6)
    roi = frame[roi_top:h, :]

    # Blur to reduce noise
    blur = cv2.GaussianBlur(
        roi,
        (5, 5),
        0
    )

    # HSV conversion
    hsv = cv2.cvtColor(
        blur,
        cv2.COLOR_BGR2HSV
    )

    # More tolerant white range
    lower_white = np.array([0, 0, 140])
    upper_white = np.array([180, 80, 255])

    mask = cv2.inRange(
        hsv,
        lower_white,
        upper_white
    )

    # Morphological cleanup
    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    # Debug mask window
    cv2.imshow("Lane Mask", mask)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:

        cv2.putText(
            frame,
            "NO LANE",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        return None, frame

    largest = max(
        contours,
        key=cv2.contourArea
    )

    area = cv2.contourArea(
        largest
    )

    # Reject small noisy contours
    if area < 2000:

        cv2.putText(
            frame,
            "LANE TOO SMALL",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        return None, frame

    # Shift contour back to full frame
    largest_global = largest.copy()
    largest_global[:, :, 1] += roi_top

    cv2.drawContours(
        frame,
        [largest_global],
        -1,
        (255, 0, 0),
        3
    )

    M = cv2.moments(
        largest
    )

    if M["m00"] == 0:
        return None, frame

    cx = int(
        M["m10"] / M["m00"]
    )

    cy = int(
        M["m01"] / M["m00"]
    )

    cx_global = cx
    cy_global = cy + roi_top

    # Follow right-side lane
    target_x = int(
        w * 0.75
    )

    cv2.circle(
        frame,
        (cx_global, cy_global),
        8,
        (0, 255, 255),
        -1
    )

    cv2.line(
        frame,
        (target_x, 0),
        (target_x, h),
        (0, 255, 0),
        2
    )

    cv2.line(
        frame,
        (cx_global, cy_global),
        (target_x, cy_global),
        (0, 0, 255),
        2
    )

    error = cx_global - target_x

    cv2.putText(
        frame,
        f"Error: {error}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Area: {int(area)}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    return error, frame


# ================= HORIZONTAL MARKER ================= #

def detect_horizontal_marker(frame):

    h, w = frame.shape[:2]

    roi_top = int(h * 0.45)
    roi_bottom = int(h * 0.65)

    roi = frame[
        roi_top:roi_bottom,
        :
    ]

    blur = cv2.GaussianBlur(
        roi,
        (5, 5),
        0
    )

    hsv = cv2.cvtColor(
        blur,
        cv2.COLOR_BGR2HSV
    )

    lower_white = np.array([0, 0, 140])
    upper_white = np.array([180, 80, 255])

    mask = cv2.inRange(
        hsv,
        lower_white,
        upper_white
    )

    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    cv2.imshow(
        "Marker Mask",
        mask
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(
            cnt
        )

        if area < 3000:
            continue

        x, y, cw, ch = cv2.boundingRect(
            cnt
        )

        aspect_ratio = cw / float(ch)

        if (
            aspect_ratio > 5
            and cw > w * 0.55
        ):

            cnt_global = cnt.copy()
            cnt_global[:, :, 1] += roi_top

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
