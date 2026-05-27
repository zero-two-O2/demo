import serial
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600

ser = None
arduino_connected = False


# ================= CONNECTION ================= #

def connect():

    global ser
    global arduino_connected

    try:

        ser = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=1
        )

        time.sleep(2)

        arduino_connected = True

        print("✅ Arduino Connected")

    except Exception as e:

        ser = None

        arduino_connected = False

        print("❌ Arduino NOT Connected")
        print(e)


# ================= SEND ================= #

def send(cmd):

    global ser
    global arduino_connected

    if arduino_connected and ser:

        try:

            ser.write((cmd + "\n").encode())

        except Exception:

            print("⚠ Lost Arduino connection")

            arduino_connected = False

            ser = None

    else:

        print(f"[SIM MODE] {cmd}")


# ================= BASIC MOVEMENT ================= #

def forward(speed=120):

    speed = max(0, min(255, int(speed)))

    send(f"F:{speed}")


def backward(speed=120):

    speed = max(0, min(255, int(speed)))

    send(f"B:{speed}")


def left():

    send("LEFT")


def right():

    send("RIGHT")


def stop():

    send("STOP")


def slow():

    send("SLOW")


# ================= ADVANCED CONTROL ================= #

def drive(speed, turn):

    """
    speed:
        -255 to +255

    turn:
        -255 to +255

    Negative turn = left
    Positive turn = right
    """

    # Deadzone

    if abs(speed) < 10:
        speed = 0

    if abs(turn) < 10:
        turn = 0

    # STOP

    if speed == 0 and turn == 0:

        stop()

        return

    # TURNING PRIORITY

    if turn > 50:

        right()

        return

    elif turn < -50:

        left()

        return

    # FORWARD / BACKWARD

    if speed > 0:

        forward(abs(speed))

    elif speed < 0:

        backward(abs(speed))