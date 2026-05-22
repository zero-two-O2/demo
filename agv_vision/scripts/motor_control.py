import serial
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600

ser = None
arduino_connected = False


def connect():
    global ser, arduino_connected

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        arduino_connected = True
        print("✅ Arduino Connected")
    except Exception as e:
        ser = None
        arduino_connected = False
        print("❌ Arduino NOT Connected")


def send(cmd):
    global ser, arduino_connected

    if arduino_connected and ser:
        try:
            ser.write((cmd + "\n").encode())
        except Exception:
            print("⚠ Lost Arduino connection")
            arduino_connected = False
            ser = None
    else:
        print(f"[SIM MODE] {cmd}")


# ---------------- MOTOR COMMANDS ---------------- #

def forward(speed):
    send(f"F:{speed}")


def backward(speed):
    send(f"B:{speed}")


def left():
    send("LEFT")


def right():
    send("RIGHT")


def stop():
    send("STOP")


def slow():
    send("SLOW")