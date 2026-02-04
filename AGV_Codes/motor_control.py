import serial
import time

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)
time.sleep(2)

def send(cmd):
    ser.write((cmd + "\n").encode())

def forward(speed):
    send(f"V{speed}")
    send("F")

def backward(speed):
    send(f"V{speed}")
    send("B")

def slow():
    send("V80")
    send("F")

def left():
    send("L")

def right():
    send("R")

def stop():
    send("X")

def up():
    send("V_UP")

def down():
    send("V_DOWN")  

def grip_close():
    send("GRIP_CLOSE")      

def grip_open():
    send("GRIP_OPEN")

def Flip(bin_type):
    send(f"FLIP_{bin_type}")

def flip_neutral():
    send("FLIP_NEUTRAL")


