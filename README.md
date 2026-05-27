# Vision-Based AGV System

## Overview
This project is a Raspberry Pi based Autonomous Guided Vehicle (AGV) system developed for intelligent navigation and automation applications.

The AGV uses computer vision techniques for:
- Lane detection
- Obstacle detection
- Path following
- Bin positioning
- Autonomous movement

The project is being developed as part of an automation and robotics engineering learning initiative.

---

## Hardware Used

- Raspberry Pi 5
- USB Camera / Pi Camera
- Motor Driver
- DC Motors
- Power Supply
- Chassis
- Ultrasonic Sensors (optional)
- Robotic Arm (future implementation)

---

## Software Stack

- Python
- OpenCV
- NumPy
- Raspberry Pi OS
- Git & GitHub

---

## Features

- Real-time camera processing
- Vision-based lane detection
- Obstacle identification
- Autonomous navigation logic
- Modular script structure
- Raspberry Pi deployment

---

## Project Structure

```bash
agv_vision/
│
├── scripts/
│   ├── lane_detection.py
│   ├── obstacle_detection.py
│   ├── camera_test.py
│   └── ...
│
├── start_agv.sh
├── mode.txt
└── README.md
