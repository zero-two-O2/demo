import cv2
import threading
import time
import signal
import sys
from collections import deque
from flask import Flask, render_template
from picamera2 import Picamera2

import motor_control as motor
from lane_detection import detect_right_lane, detect_horizontal_marker
from bin_detection import detect_bin   # 
from libcamera import Transform   # Add this import at top





# ================= CONFIG ================= #

MODE_FILE = "/home/zerotwo/agv_vision/mode.txt"

current_speed = 120
command_log = deque(maxlen=20)

auto_state = "DRIVING"
bin_request = False
use_side_camera = False


# ================= LOGGING ================= #

def log_cmd(msg):
    ts = time.strftime("%H:%M:%S")
    command_log.append(f"[{ts}] {msg}")
    print(msg)


def read_mode():
    try:
        return open(MODE_FILE).read().strip()
    except:
        return "MANUAL"


def set_mode(m):
    global auto_state, bin_request, use_side_camera
    open(MODE_FILE, "w").write(m)
    motor.stop()
    auto_state = "DRIVING"
    bin_request = False
    use_side_camera = False
    log_cmd(f"MODE → {m}")


# ================= ARDUINO ================= #

motor.connect()
if not motor.arduino_connected:
    log_cmd("ARDUINO NOT CONNECTED → SIM MODE")


# ================= FRONT CAMERA ================= #


picam_front = Picamera2(0)
picam_front.configure(
    picam_front.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)},
        transform=Transform(vflip=True)   # FIX: Vertical Flip
    )
)
picam_front.start()

cv2.namedWindow("AGV FRONT CAMERA", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AGV FRONT CAMERA", 800, 600)


# ================= SIDE CAMERA (ALWAYS RUNNING) ================= #

picam_side = Picamera2(1)
picam_side.configure(
    picam_side.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)
picam_side.start()

cv2.namedWindow("AGV SIDE CAMERA", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AGV SIDE CAMERA", 500, 400)
cv2.destroyWindow("AGV SIDE CAMERA")  # Hide initially


# ================= FLASK ================= #

app = Flask(__name__)


@app.route("/set_mode/<mode>")
def change_mode(mode):
    set_mode(mode)
    return "OK"


@app.route("/manual/<cmd>")
def manual_cmd(cmd):
    if read_mode() == "MANUAL":
        if cmd == "FORWARD":
            motor.forward(120)
        elif cmd == "BACKWARD":
            motor.backward(120)
        elif cmd == "LEFT":
            motor.left()
        elif cmd == "RIGHT":
            motor.right()
        elif cmd == "STOP":
            motor.stop()
        log_cmd(f"MANUAL → {cmd}")
    return "OK"


@app.route("/side_camera/<action>")
def side_camera_control(action):
    global use_side_camera

    if read_mode() == "MANUAL":
        if action == "ON":
            use_side_camera = True
            log_cmd("SIDE CAMERA DISPLAY ON")
        elif action == "OFF":
            use_side_camera = False
            cv2.destroyWindow("AGV SIDE CAMERA")
            log_cmd("SIDE CAMERA DISPLAY OFF")

    return "OK"


@app.route("/start_bin_sequence")
def start_bin_sequence():
    global bin_request

    if read_mode() == "AUTO":
        bin_request = True
        log_cmd("BIN SEQUENCE REQUESTED FROM WEB")
    return "OK"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logs")
def logs():
    return "\n".join(command_log)


# ================= CLEANUP ================= #

def cleanup(sig=None, frame=None):
    print("Shutting down...")

    picam_front.stop()
    picam_front.close()

    picam_side.stop()
    picam_side.close()

    cv2.destroyAllWindows()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


# ================= MAIN LOOP ================= #

def vision_loop():
    global auto_state, current_speed, bin_request, use_side_camera

    while True:

        frame_front = picam_front.capture_array()
        marker, frame_front = detect_horizontal_marker(frame_front)

        frame_side = picam_side.capture_array()

        # ---------------- AUTO MODE ---------------- #
        if read_mode() == "AUTO":

            if auto_state == "DRIVING":

                if marker or bin_request:
                    motor.stop()
                    auto_state = "BIN_SEQUENCE"
                    use_side_camera = True
                    log_cmd("ENTERING BIN SEQUENCE")

                else:
                    error, frame_front = detect_right_lane(frame_front)

                    if error is None:
                        motor.stop()
                    elif error > 50:
                        motor.right()
                    elif error < -50:
                        motor.left()
                    else:
                        motor.forward(current_speed)

            elif auto_state == "BIN_SEQUENCE":

                bin_color = detect_bin(frame_side)   # UPDATED CALL

                if bin_color:
                    log_cmd(f"BIN DETECTED → {bin_color}")

                    motor.send(f"FLIP_{bin_color}")
                    time.sleep(2)
                    motor.send("FLIP_NEUTRAL")
                    time.sleep(1)

                    use_side_camera = False
                    bin_request = False
                    auto_state = "DRIVING"
                    log_cmd("BIN SEQUENCE COMPLETE")

        # ---------------- DISPLAY ---------------- #

        cv2.imshow("AGV FRONT CAMERA", frame_front)

        if use_side_camera:
            cv2.imshow("AGV SIDE CAMERA", frame_side)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cleanup()


# ================= START ================= #

if __name__ == "__main__":

    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5000),
        daemon=True
    )
    flask_thread.start()

    log_cmd("SYSTEM STARTED")

    vision_loop()