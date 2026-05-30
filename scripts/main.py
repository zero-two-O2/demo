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

from lane_detection import detect_right_lane
from bin_detection import detect_bin


# ================= CONFIG ================= #


current_speed = 120

command_log = deque(maxlen=50)

last_x_button = 0
last_y_button = 0
bin_detection_active = False
detected_bin = None
last_lt = False
last_rt = False

# ================= CONTROL ================= #

controller_connected = False
controller_enabled = False


# ================= COMMAND STATES ================= #

last_drive_command = ""

last_horizontal_command = ""

last_vertical_command = ""

last_gripper_command = ""

last_flipper_command = ""


# ================= GPS ================= #

gps_data = {
    "latitude": 19.6131,
    "longitude": 74.1859,
    "speed": 0,
    "heading": 0
}


# ================= LOGGING ================= #

def log_cmd(msg):

    ts = time.strftime("%H:%M:%S")

    entry = f"[{ts}] {msg}"

    # Avoid duplicate spam

    if len(command_log) > 0:

        if command_log[-1] == entry:

            return

    command_log.append(entry)

    print(entry)


# ================= MODE ================= #

current_mode = "MANUAL"


def read_mode():

    global current_mode

    return current_mode


def set_mode(m):

    global current_mode
    global controller_enabled
    global last_drive_command

    current_mode = m

    controller_enabled = (m == "MANUAL")

    last_drive_command = ""

    motor.stop()

    if m == "AUTO":

        motor.send("A")

    elif m == "MANUAL":

        motor.send("W")

    log_cmd(f"MODE → {m}")
    



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

                except Exception as e:

                    print("JSON ERROR:", e)

            buffer = packets[-1]

        except Exception as e:

            print("GPS CONNECTION ERROR:", e)

            time.sleep(1)


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

    if read_mode() != "MANUAL":

        return "NOT MANUAL MODE"

    if cmd == "FORWARD":

        motor.forward()

        log_cmd("WEB → FORWARD")

    elif cmd == "BACKWARD":

        motor.backward()

        log_cmd("WEB → BACKWARD")

    elif cmd == "LEFT":

        motor.left()

        log_cmd("WEB → LEFT")

    elif cmd == "RIGHT":

        motor.right()

        log_cmd("WEB → RIGHT")

    elif cmd == "STOP":

        motor.stop()

        log_cmd("WEB → STOP")

    return "OK"


# ================= CONTROL SOURCE ================= #

@app.route("/enable_gamepad")
def enable_gamepad():

    global controller_enabled

    controller_enabled = True

    log_cmd("GAMEPAD ENABLED")

    return "OK"


@app.route("/enable_web")
def enable_web():

    global controller_enabled

    controller_enabled = False

    motor.stop()

    log_cmd("WEB CONTROL ENABLED")

    return "OK"


@app.route("/controller_status")
def controller_status():

    return {
        "connected": controller_connected,
        "enabled": controller_enabled
    }


@app.route("/pickup")
def pickup():

    global bin_detection_active
    global detected_bin

    detected_bin = None

    bin_detection_active = True

    motor.auto_lift()

    log_cmd("PICKUP SEQUENCE STARTED")

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

    global controller_enabled

    global last_drive_command
    global last_horizontal_command
    global last_vertical_command
    global last_gripper_command
    global last_flipper_command
    global last_lt
    global last_rt
    global bin_detection_active
    global detected_bin

    DEADZONE = 0.15

    while True:

        try:

            if not controller_connected:

                time.sleep(1)

                continue

            pygame.event.pump()

            # ================= LEFT STICK =================

            left_y = joystick.get_axis(1)

            left_x = joystick.get_axis(0)

            if abs(left_y) < DEADZONE:
                left_y = 0

            if abs(left_x) < DEADZONE:
                left_x = 0

            # ================= RIGHT STICK =================

            # These may need adjustment after jstest

            right_x = joystick.get_axis(2)

            right_y = joystick.get_axis(3)

            if abs(right_x) < DEADZONE:
                right_x = 0

            if abs(right_y) < DEADZONE:
                right_y = 0

            # ================= BUTTONS =================

            A_BUTTON = joystick.get_button(0)

            B_BUTTON = joystick.get_button(1)

            X_BUTTON = joystick.get_button(3)

            Y_BUTTON = joystick.get_button(4)

            # ================= D PAD =================

            hat = joystick.get_hat(0)

            dpad_x = hat[0]

            # ================= RT TRIGGER =================

            rt_trigger = joystick.get_axis(5)
            lt_trigger = joystick.get_axis(4)

            # ================= MODE CONTROL =================

            if X_BUTTON:

                set_mode("MANUAL")

                controller_enabled = True

                log_cmd("CONTROLLER → MANUAL MODE")

                time.sleep(0.3)

            if Y_BUTTON:

                set_mode("AUTO")

                controller_enabled = False

                log_cmd("CONTROLLER → AUTO MODE")

                time.sleep(0.3)

            lt_pressed = lt_trigger > 0.8
            if lt_pressed and not last_lt:
                log_cmd("LT Pressed")    
                detected_bin = None
                bin_detection_active = True
                motor.auto_lift()
                log_cmd("PICKUP SEQUENCE STARTED")
            last_lt = lt_pressed
            
            rt_pressed = rt_trigger > 0.8
            if rt_pressed and not last_rt:
                motor.abort_lift()
                bin_detection_active = False
                detected_bin = None
                log_cmd("PICKUP SEQUENCE ABORTED")
            
            last_rt = rt_pressed
             
                
            
            
            # ================= EMERGENCY STOP =================

            if rt_trigger > 0.8:

                motor.stop()

                if last_drive_command != "STOP":

                    log_cmd("EMERGENCY STOP")

                    last_drive_command = "STOP"

                time.sleep(0.1)

                continue

            # ================= DRIVE =================

            if (
                read_mode() == "MANUAL"
                and controller_enabled
            ):

                if left_y < -0.5:

                    if last_drive_command != "FORWARD":

                        motor.forward()

                        log_cmd("MOVE → FORWARD")

                        last_drive_command = "FORWARD"

                elif left_y > 0.5:

                    if last_drive_command != "BACKWARD":

                        motor.backward()

                        log_cmd("MOVE → BACKWARD")

                        last_drive_command = "BACKWARD"

                elif left_x < -0.5:

                    if last_drive_command != "LEFT":

                        motor.left()

                        log_cmd("MOVE → LEFT")

                        last_drive_command = "LEFT"

                elif left_x > 0.5:

                    if last_drive_command != "RIGHT":

                        motor.right()

                        log_cmd("MOVE → RIGHT")

                        last_drive_command = "RIGHT"

                else:

                    if last_drive_command != "STOP":

                        motor.stop()

                        log_cmd("MOVE → STOP")

                        last_drive_command = "STOP"

            # ================= HORIZONTAL ARM =================

            if right_x > 0.5:

                if last_horizontal_command != "HF":

                    motor.horizontal_forward()

                    log_cmd(
                        "ARM → HORIZONTAL FORWARD"
                    )

                    last_horizontal_command = "HF"

            elif right_x < -0.5:

                if last_horizontal_command != "HR":

                    motor.horizontal_reverse()

                    log_cmd(
                        "ARM → HORIZONTAL REVERSE"
                    )

                    last_horizontal_command = "HR"

            else:

                if last_horizontal_command != "HS":

                    motor.horizontal_stop()

                    last_horizontal_command = "HS"

            # ================= VERTICAL ARM =================

            if right_y < -0.5:

                if last_vertical_command != "VU":

                    motor.vertical_up()

                    log_cmd("ARM → UP")

                    last_vertical_command = "VU"

            elif right_y > 0.5:

                if last_vertical_command != "VD":

                    motor.vertical_down()

                    log_cmd("ARM → DOWN")

                    last_vertical_command = "VD"

            else:

                if last_vertical_command != "VS":

                    motor.vertical_stop()

                    last_vertical_command = "VS"

            # ================= GRIPPER =================

            if dpad_x == -1:

                if last_gripper_command != "OPEN":

                    motor.gripper_open()

                    log_cmd("GRIPPER → OPEN")

                    last_gripper_command = "OPEN"

            elif dpad_x == 1:

                if last_gripper_command != "CLOSE":

                    motor.gripper_close()

                    log_cmd("GRIPPER → CLOSE")

                    last_gripper_command = "CLOSE"

            # ================= FLIPPER =================

            if A_BUTTON:

                if last_flipper_command != "LEFT":

                    motor.flipper_left()

                    log_cmd("FLIPPER → LEFT")

                    last_flipper_command = "LEFT"

            if B_BUTTON:

                if last_flipper_command != "RIGHT":

                    motor.flipper_right()

                    log_cmd("FLIPPER → RIGHT")

                    last_flipper_command = "RIGHT"

            time.sleep(0.03)

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

    while True:

        frame_front = picam_front.capture_array()
        frame_side = picam_side.capture_array()
        global bin_detection_active
        global detected_bin
        if bin_detection_active:
            log_cmd("SIDE CAMERA ACTIVE")
            bin_color = detect_bin(frame_side)
            if (
            bin_color is not None
            and detected_bin is None
            ):
                detected_bin = bin_color
                log_cmd(
                f"BIN DETECTED → {bin_color}"
                )
                if bin_color == "WET":
                    motor.flipper_left()
                    log_cmd(
                    "FLIPPER → WET"
                    )
                elif bin_color == "DRY":
                    motor.flipper_right()
                    log_cmd(
                    "FLIPPER → DRY"
                    )
                bin_detection_active = False
                detected_bin = None
        
        
        if read_mode() == "AUTO":

            error, frame_front = detect_right_lane(
                frame_front
            )

            if error is not None:

                cv2.putText(
                    frame_front,
                    "LANE DETECTED",
                    (20,120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2
                )

            else:

                cv2.putText(
                    frame_front,
                    "NO LANE",
                    (20,120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,255),
                    2
                )
         
        if bin_detection_active:
             cv2.namedWindow(
             "AGV SIDE CAMERA",
             cv2.WINDOW_NORMAL
             )
             cv2.imshow(
             "AGV SIDE CAMERA",
             frame_side
             )
        else:
            try:
                cv2.destroyWindow(
                "AGV SIDE CAMERA"
                )
            except:
                pass
        
        cv2.imshow(
            "AGV FRONT CAMERA",
            frame_front
        )

        if cv2.waitKey(1) & 0xFF == ord('q'):

            cleanup()


# ================= START ================= #

if __name__ == "__main__":

#    gps_thread = threading.Thread(
#        target=gps_receiver,
#        daemon=True
#    )
#
#    gps_thread.start()

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
