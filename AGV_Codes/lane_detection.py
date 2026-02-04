import cv2
import numpy as np

def detect_horizontal_marker(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 200), (180, 40, 255))
    edges = cv2.Canny(mask, 50, 150)

    lines = cv2.HoughLinesP(edges, 1, np.pi/180,
                            threshold=100,
                            minLineLength=150,
                            maxLineGap=20)

    if lines is not None:
        for x1, y1, x2, y2 in lines[:,0]:
            if abs(y1 - y2) < 10:
                return True, frame
    return False, frame

def detect_right_lane(frame):
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, (0,0,180), (180,40,255))
    roi = np.zeros_like(mask)
    roi[:, int(w*0.5):] = 255
    mask = cv2.bitwise_and(mask, roi)

    edges = cv2.Canny(mask, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180,
                            threshold=80,
                            minLineLength=100,
                            maxLineGap=50)

    xs = []
    if lines is not None:
        for x1,y1,x2,y2 in lines[:,0]:
            if abs(x1 - x2) < 20:
                xs.append(x1)

    if not xs:
        return None, frame

    avg_x = int(sum(xs)/len(xs))
    target = int(w*0.75)
    return avg_x - target, frame
