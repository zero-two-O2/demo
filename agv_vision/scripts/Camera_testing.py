import cv2
import time
from picamera2 import Picamera2

# ---------------- FRONT CAMERA ---------------- #

def start_camera(cam_id, width, height):
    cam = Picamera2(cam_id)
    cam.configure(
        cam.create_video_configuration(
            main={"format": "RGB888", "size": (width, height)}
        )
    )
    cam.start()
    time.sleep(1)
    return cam


try:
    print("Starting Front Camera (ID 0)...")
    cam_front = start_camera(0, 640, 480)
    print("Front Camera OK")

except Exception as e:
    print("Front Camera FAILED:", e)
    cam_front = None


try:
    print("Starting Side Camera (ID 1)...")
    cam_side = start_camera(1, 320, 240)
    print("Side Camera OK")

except Exception as e:
    print("Side Camera FAILED:", e)
    cam_side = None


cv2.namedWindow("Front Camera", cv2.WINDOW_NORMAL)
cv2.namedWindow("Side Camera", cv2.WINDOW_NORMAL)

while True:
    if cam_front:
        frame_front = cam_front.capture_array()
        cv2.imshow("Front Camera", frame_front)

    if cam_side:
        frame_side = cam_side.capture_array()
        cv2.imshow("Side Camera", frame_side)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


print("Shutting down...")

if cam_front:
    cam_front.stop()
    cam_front.close()

if cam_side:
    cam_side.stop()
    cam_side.close()

cv2.destroyAllWindows()