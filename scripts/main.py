import cv2
import threading
import time
import signal
import sys
import socket
import json
import pygame

from collections import deque
from flask import Flask, render_template

from picamera2 import Picamera2
from libcamera import Transform

import motor_control as motor
from lane_detection import detect_right_lane, detect_horizontal_marker
from bin_detection import detect_bin


# ================= CONFIG ================= #

MODE_FILE = "/home/zerotwo/agv_vision/mode.txt"

current_speed = 120
command_log = deque(maxlen=20)

auto_state = "DRIVING"
bin_request = False
use_side_camera = False


# ================= CONTROL ================= #

manual_speed = 0
manual_turn = 0

controller_connected = False
controller_enabled = False


# ================= GPS ================= #

gps_data = {
    "latitude": 19.6131,
    "longitude": 74.1859,
    "speed": 0,
    "heading": 0
}


# ================= GPS RECEIVER ================= #

def gps_receiver():

    PHONE_IP = "10.67.217.4"
    PORT = 5005

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    print("Connecting to GPS server...")

    sock.connect((PHONE_IP, PORT))

    print("GPS CONNECTED!")

    buffer = ""

    while True:

        try:

            data = sock.recv(4096)

            if not data:
                break

            buffer += data.decode(errors="ignore")

            packets = buffer.split("}")

            for packet in packets[:-1]:

                packet = packet + "}"

                try:

                    gps = json.loads(packet)

                    gps_data["latitude"] = gps["latitude"]
                    gps_data["longitude"] = gps["longitude"]
                    gps_data["speed"] = gps["speed"]
                    gps_data["heading"] = gps["heading"]

                    print(
                        f"GPS → "
                        f"{gps_data['latitude']}, "
                        f"{gps_data['longitude']}"
                    )

                except Exception as e:

                    print("JSON ERROR:", e)

            buffer = packets[-1]

        except Exception as e:

            print("GPS CONNECTION ERROR:", e)

            time.sleep(1)


# ================= LOGGING ================= #

def log_cmd(msg):

    ts = time.strftime("%H:%M:%S")

    command_log.append(f"[{ts}] {msg}")

    print(msg)


# ================= MODE ================= #

def read_mode():

    try:

        return open(MODE_FILE).read().strip()

    except:

        return "MANUAL"


def set_mode(m):

    global auto_state
    global bin_request
    global use_side_camera
    global manual_speed
    global manual_turn
    global controller_enabled

    open(MODE_FILE, "w").write(m)

    motor.stop()

    manual_speed = 0
    manual_turn = 0

    controller_enabled = False

    auto_state = "DRIVING"

    bin_request = False

    use_side_camera = False

    log_cmd(f"MODE → {m}")


# ================= ARDUINO ================= #

motor.connect()

if not motor.arduino_connected:

    log_cmd("ARDUINO NOT CONNECTED → SIM MODE")


# ================= GAMEPAD ================= #

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() > 0:

    joystick = pygame.joystick.Joystick(0)

    joystick.init()

    controller_connected = True

    log_cmd(
        f"GAMEPAD CONNECTED → "
        f"{joystick.get_name()}"
    )

else:

    log_cmd("NO GAMEPAD DETECTED")


# ================= FRONT CAMERA ================= #

picam_front = Picamera2(0)

picam_front.configure(
    picam_front.create_video_configuration(
        main={
            "format": "RGB888",
            "size": (640, 480)
        },
        transform=Transform(vflip=True)
    )
)

picam_front.start()

cv2.namedWindow(
    "AGV FRONT CAMERA",
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    "AGV FRONT CAMERA",
    800,
    600
)


# ================= SIDE CAMERA ================= #

picam_side = Picamera2(1)

picam_side.configure(
    picam_side.create_video_configuration(
        main={
            "format": "RGB888",
            "size": (640, 480)
        }
    )
)

picam_side.start()

cv2.namedWindow(
    "AGV SIDE CAMERA",
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    "AGV SIDE CAMERA",
    500,
    400
)

cv2.destroyWindow("AGV SIDE CAMERA")


# ================= FLASK ================= #

app = Flask(__name__)


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/set_mode/<mode>")
def change_mode(mode):

    set_mode(mode)

    return "OK"


# ================= WEB CONTROL ================= #

@app.route("/manual/<cmd>")
def manual_cmd(cmd):

    global manual_speed
    global manual_turn

    if read_mode() != "MANUAL":

        return "NOT MANUAL MODE"

    # Ignore web control if gamepad active
    if controller_enabled:

        return "GAMEPAD ACTIVE"

    if cmd == "FORWARD":

        manual_speed = 120
        manual_turn = 0

    elif cmd == "BACKWARD":

        manual_speed = -120
        manual_turn = 0

    elif cmd == "LEFT":

        manual_speed = 80
        manual_turn = -100

    elif cmd == "RIGHT":

        manual_speed = 80
        manual_turn = 100

    elif cmd == "STOP":

        manual_speed = 0
        manual_turn = 0

        motor.stop()

    log_cmd(f"WEB CONTROL → {cmd}")

    return "OK"


# ================= CONTROLLER SWITCH ================= #

@app.route("/enable_gamepad")
def enable_gamepad():

    global controller_enabled

    controller_enabled = True

    motor.stop()

    log_cmd("GAMEPAD CONTROL ENABLED")

    return "OK"


@app.route("/enable_web")
def enable_web():

    global controller_enabled
    global manual_speed
    global manual_turn

    controller_enabled = False

    manual_speed = 0
    manual_turn = 0

    motor.stop()

    log_cmd("WEB CONTROL ENABLED")

    return "OK"


@app.route("/controller_status")
def controller_status():

    return {
        "connected": controller_connected,
        "enabled": controller_enabled
    }


# ================= SIDE CAMERA ================= #

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


# ================= BIN CONTROL ================= #

@app.route("/start_bin_sequence")
def start_bin_sequence():

    global bin_request

    if read_mode() == "AUTO":

        bin_request = True

        log_cmd("BIN SEQUENCE REQUESTED FROM WEB")

    return "OK"


# ================= GPS ================= #

@app.route("/gps")
def gps():

    return gps_data


# ================= LOGS ================= #

@app.route("/logs")
def logs():

    return "\n".join(command_log)


# ================= GAMEPAD LOOP ================= #

def gamepad_loop():

    global manual_speed
    global manual_turn
    global controller_enabled

    DEADZONE = 0.15

    while True:

        try:

            if read_mode() != "MANUAL":

                time.sleep(0.1)

                continue

            if not controller_connected:

                time.sleep(1)

                continue

            pygame.event.pump()

            # LEFT STICK

            y_axis = joystick.get_axis(1)
            x_axis = joystick.get_axis(0)

            # DEADZONE

            if abs(y_axis) < DEADZONE:

                y_axis = 0

            if abs(x_axis) < DEADZONE:

                x_axis = 0

            # ENABLE GAMEPAD - A BUTTON

            if joystick.get_button(0):

                if not controller_enabled:

                    controller_enabled = True

                    motor.stop()

                    log_cmd("GAMEPAD CONTROL ENABLED")

                time.sleep(0.3)

            # ENABLE WEB - B BUTTON

            if joystick.get_button(1):

                if controller_enabled:

                    controller_enabled = False

                    manual_speed = 0
                    manual_turn = 0

                    motor.stop()

                    log_cmd("WEB CONTROL ENABLED")

                time.sleep(0.3)

            # ONLY CONTROL IF ENABLED

            if controller_enabled:

                manual_speed = int(-y_axis * 120)

                manual_turn = int(x_axis * 100)

            time.sleep(0.02)

        except Exception as e:

            print("GAMEPAD ERROR:", e)

            time.sleep(1)


# ================= CLEANUP ================= #

def cleanup(sig=None, frame=None):

    print("Shutting down...")

    motor.stop()

    picam_front.stop()
    picam_front.close()

    picam_side.stop()
    picam_side.close()

    cv2.destroyAllWindows()

    pygame.quit()

    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


# ================= MAIN LOOP ================= #

def vision_loop():

    global auto_state
    global current_speed
    global bin_request
    global use_side_camera

    while True:

        frame_front = picam_front.capture_array()

        marker, frame_front = detect_horizontal_marker(
            frame_front
        )

        frame_side = picam_side.capture_array()

        # ================= AUTO MODE ================= #

        if read_mode() == "AUTO":

            if auto_state == "DRIVING":

                if marker or bin_request:

                    motor.stop()

                    auto_state = "BIN_SEQUENCE"

                    use_side_camera = True

                    log_cmd("ENTERING BIN SEQUENCE")

                else:

                    error, frame_front = detect_right_lane(
                        frame_front
                    )

                    if error is None:

                        motor.stop()

                    elif error > 50:

                        motor.right()

                    elif error < -50:

                        motor.left()

                    else:

                        motor.forward(current_speed)

            elif auto_state == "BIN_SEQUENCE":

                bin_color = detect_bin(frame_side)

                if bin_color:

                    log_cmd(
                        f"BIN DETECTED → {bin_color}"
                    )

                    motor.send(f"FLIP_{bin_color}")

                    time.sleep(2)

                    motor.send("FLIP_NEUTRAL")

                    time.sleep(1)

                    use_side_camera = False

                    bin_request = False

                    auto_state = "DRIVING"

                    log_cmd(
                        "BIN SEQUENCE COMPLETE"
                    )

        # ================= MANUAL MODE ================= #

        elif read_mode() == "MANUAL":

            motor.drive(
                manual_speed,
                manual_turn
            )

        # ================= DISPLAY ================= #

        cv2.imshow(
            "AGV FRONT CAMERA",
            frame_front
        )

        if use_side_camera:

            cv2.imshow(
                "AGV SIDE CAMERA",
                frame_side
            )

        if cv2.waitKey(1) & 0xFF == ord('q'):

            cleanup()


# ================= START ================= #

if __name__ == "__main__":

    gps_thread = threading.Thread(
        target=gps_receiver,
        daemon=True
    )

    gps_thread.start()

    flask_thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=5000
        ),
        daemon=True
    )

    flask_thread.start()

    gamepad_thread = threading.Thread(
        target=gamepad_loop,
        daemon=True
    )

    gamepad_thread.start()

    log_cmd("SYSTEM STARTED")

    vision_loop()