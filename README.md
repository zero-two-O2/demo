# AGCV Project

Autonomous Garbage Collection Vehicle (AGCV) using Raspberry Pi, Arduino, OpenCV, lane detection, ArUco markers, and dustbin color detection.

---

## Features

- Side white-line following
- Horizontal reference line detection
- Dustbin color detection
- ArUco marker detection
- Ultrasonic obstacle avoidance
- Web controller
- Manual + autonomous mode

---

## Hardware Used

- Raspberry Pi 4
- Arduino
- Logitech C270 / Pi Camera
- Ultrasonic Sensor
- Motor Driver
- DC Motors
- Battery Pack

---

## Software Used

- Python
- OpenCV
- NumPy
- Flask
- Arduino IDE

---

## Run Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Run main code:

```bash
python main.py
```

---

## Important Notes

- Vehicle stops if no white line is detected
- Using side lane as reference
- OpenCV used for all camera processing
- No YOLO used
- GPS/RFID not used
- Autonomous navigation not fully tested

---

## Folder Structure

```text
main.py              -> Main AGCV control code
arduino_code/        -> Arduino motor control code
web_controller/      -> Web controller files
images/              -> Test images
videos/              -> Test videos
```

---

## Problems Faced

- Motor drivers getting damaged frequently
- Wiring had to be redone multiple times
- Lane detection affected by lighting
- Arduino got short-circuited and replaced

---

## Future Improvements

- Better autonomous navigation
- Improved lane stability
- SLAM/path planning
- Better power management
- Improved obstacle avoidance

---
