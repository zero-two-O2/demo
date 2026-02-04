import cv2
import threading
import time
from collections import deque
from flask import Flask, render_template, Response
from picamera2 import Picamera2
import motor_control as motor
from lane_detection import detect_right_lane, detect_horizontal_marker
from bin_detection import detect_bin_color


MODE_FILE = "/home/zerotwo/agv_vision/mode.txt"

current_speed = 120
command_log = deque(maxlen=10)


auto_state = "DRIVING"  

bin_detect_start = 0
BIN_DETECT_TIMEOUT = 5.0  # seconds

bin_type = None
bin_done = False

side_camera_active = False
ir_triggered = False
ultrasonic_distance = None


def log_cmd(msg):
    ts = time.strftime("%H:%M:%S")
    command_log.append(f"[{ts}] {msg}")


def read_mode():
    try:
        return open(MODE_FILE).read().strip()
    except:
        return "MANUAL"

def set_mode(m):
    open(MODE_FILE, "w").write(m)
    motor.stop()

picam_front = Picamera2(0)
picam_front.configure(
    picam_front.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)
picam_front.start()

picam_side = None
latest_front = None
latest_side = None
frame_lock = threading.Lock()

def start_side_camera():
    global picam_side, side_camera_active
    if side_camera_active:
        return
    picam_side = Picamera2(1)
    picam_side.configure(
        picam_side.create_video_configuration(
            main={"format": "RGB888", "size": (320, 240)}
        )
    )
    picam_side.start()
    side_camera_active = True
    log_cmd("SIDE CAMERA ON")

def stop_side_camera():
    global picam_side, side_camera_active, latest_side
    if not side_camera_active:
        return
    picam_side.stop()
    picam_side.close()
    picam_side = None
    latest_side = None
    side_camera_active = False
    log_cmd("SIDE CAMERA OFF") 



app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_front")
def video_front():
    def gen():
        while True:
            with frame_lock:
                if latest_front is None:
                    continue
                _, jpg = cv2.imencode(".jpg", latest_front)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" +
                       jpg.tobytes() + b"\r\n")
    return Response(gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/video_side")
def video_side():
    if not side_camera_active or latest_side is None:
        return Response(status=204)

    def gen():
        while side_camera_active:
            with frame_lock:
                if latest_side is None:
                    continue
                _, jpg = cv2.imencode(".jpg", latest_side)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" +
                       jpg.tobytes() + b"\r\n")
    return Response(gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/logs")
def logs():
    return "\n".join(command_log)


def serial_listener():
    global ir_triggered, ultrasonic_distance
    while True:
        line = motor.ser.readline().decode().strip()
        if line == "IR_MARKER":
            ir_triggered = True
            log_cmd("IR MARKER DETECTED")

        elif line.startswith("ULTRASONIC:"):
            try:
                dist = float(line.split(":")[1])
                ultrasonic_distance = dist
            except:
                pass

serial_thread = threading.Thread(target=serial_listener, daemon=True)
serial_thread.start()




def vision_loop():
    global latest_front, latest_side
    global current_speed, auto_state
    global bin_type, bin_done, ir_triggered

    while True:
        frame = picam_front.capture_array()
        marker, frame = detect_horizontal_marker(frame)

        if read_mode() == "AUTO":

            if auto_state == "DRIVING":
                if marker:
                    auto_state = "SLOW"
                    current_speed = 50
                    motor.slow()
                    log_cmd("MARKER DETECTED → SLOW")

                else:
                    error, frame = detect_right_lane(frame)
                    if error is None:
                        motor.stop()
                    elif error > 50:
                        motor.right()
                    elif error < -50:
                        motor.left()
                    else:
                        motor.forward(current_speed)
                    log_cmd(f"DRIVING → ERROR: {error}")


            elif auto_state == "SLOW":
                if ir_triggered:
                    motor.stop()
                    auto_state = "BIN_SEQUENCE"
                    log_cmd("IR CONFIRMED → STOP & BIN SEQUENCE")
                    start_side_camera()


            elif auto_state == "BIN_SEQUENCE":
                frame_side = picam_side.capture_array()
                bin_color = detect_bin_color(frame_side)

                if bin_color and not bin_done:
                    bin_type = bin_color
                    motor.send(f"FLIP_{bin_type}")
                    log_cmd(f"BIN TYPE → {bin_type}")
                    time.sleep(2)

                    motor.send("FLIP_NEUTRAL")
                    log_cmd("FLIP → NEUTRAL")
                    time.sleep(1)

                    bin_done = True
                    stop_side_camera()
                    ir_triggered = False
                    auto_state = "DRIVING"
                    log_cmd("BIN DONE → RESUME DRIVE")


            elif auto_state  == "ERROR":
                motor.stop()
                log_cmd("ERROR STATE → STOPPED")        

        with frame_lock:
            latest_front = frame.copy()
            if side_camera_active:
                latest_side = frame_side.copy() if 'frame_side' in locals() else None

        time.sleep(0.03)



if __name__ == "__main__":
    set_mode("MANUAL")
    log_cmd("SYSTEM STARTED")

    t = threading.Thread(target=vision_loop, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5000, threaded=True)
