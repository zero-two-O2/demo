import cv2
import numpy as np
from picamera2 import Picamera2

picam = Picamera2(1)
picam.configure(
    picam.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)
picam.start()

print("Side camera started. Press Q to quit.")

# ================= HSV RANGES =================
BLUE_LOWER  = np.array([100, 150, 80])
BLUE_UPPER  = np.array([130, 255, 255])

GREEN_LOWER = np.array([40, 120, 80])
GREEN_UPPER = np.array([85, 255, 255])

SKIN_LOWER  = np.array([0, 20, 70])
SKIN_UPPER  = np.array([20, 150, 255])

MIN_AREA = 6000

while True:
    frame = picam.capture_array()
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    blue_mask  = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    green_mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)

    skin_mask = cv2.inRange(hsv, SKIN_LOWER, SKIN_UPPER)

    blue_mask  = cv2.bitwise_and(blue_mask,  cv2.bitwise_not(skin_mask))
    green_mask = cv2.bitwise_and(green_mask, cv2.bitwise_not(skin_mask))

    detected = None

    for mask, label, color in [
        (blue_mask,  "WET BIN", (255, 0, 0)),
        (green_mask, "DRY BIN", (0, 255, 0))
    ]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)
            if area < MIN_AREA:
                continue

            x, y, w, h = cv2.boundingRect(c)
            aspect = w / float(h)

            if aspect < 0.5 or aspect > 2.0:
                continue

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(
                frame, label, (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2
            )
            detected = True
            break

        if detected:
            break

    cv2.imshow("Side Camera - Bin Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam.stop()
cv2.destroyAllWindows()
print("Camera stopped.")
