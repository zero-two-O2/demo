import serial
import time

SERIAL_PORT = "/dev/ttyACM0"
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

    
            ser.write(cmd.encode())
            ser.flush()
            

        except Exception:

            print("⚠ Lost Arduino connection")

            arduino_connected = False

            ser = None

    else:

        print(f"[SIM MODE] {cmd}")


# ================= DRIVE ================= #

def forward(speed=120):

    send("F")


def backward(speed=120):

    send("B")


def left():

    send("L")


def right():

    send("R")


def stop():

    send("S")


# ================= AUTO LIFT ================= #

def auto_lift():

    send("D")
    
def abort_lift():

    send("X")

# ================= HORIZONTAL ARM ================= #

def horizontal_forward():

    send("H")


def horizontal_reverse():

    send("J")


def horizontal_stop():

    send("K")


# ================= VERTICAL ARM ================= #

def vertical_up():

    send("U")


def vertical_down():

    send("N")


def vertical_stop():

    send("M")


# ================= GRIPPER ================= #

def gripper_open():

    send("C")


def gripper_close():

    send("O")


# ================= FLIPPER ================= #

def flipper_left():

    send("P")


def flipper_right():

    send("Q")


# ================= MAIN DRIVE LOGIC ================= #

def drive(speed, turn):

    # Deadzone

    if abs(speed) < 10:
        speed = 0

    if abs(turn) < 10:
        turn = 0

    # STOP

    if speed == 0 and turn == 0:

        stop()

        return

    # TURNING

    if turn > 40:

        right()

        return

    elif turn < -40:

        left()

        return

    # FORWARD / BACKWARD

    if speed > 0:

        forward()

    elif speed < 0:

        backward()
