import cv2, numpy as np, time
import yt_dlp as yt
from ultralytics import YOLO


VIDEO = "inputs/video.mkv"    # or 0 for webcam
MIN_AREA = 3000        # pixels; tune per resolution
COOLDOWN = 0.4         # seconds between alerts



cap = cv2.VideoCapture(VIDEO)
fg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
last_alert = 0
motion_on = False
t_start = None

# YOLO object detection system
model = YOLO('yolo11n.pt')

def now(): return time.time()
def ts(sec): return f"{sec:.2f}s"

while True:
    ok, frame = cap.read()
    if not ok: break
    mask = fg.apply(frame)                 # foreground mask
    mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)[1]
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3),np.uint8), iterations=1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    moving = sum(cv2.contourArea(c) for c in cnts if cv2.contourArea(c) > MIN_AREA) > 0

    if moving and not motion_on and now()-last_alert > COOLDOWN:
        motion_on = True; t_start = cap.get(cv2.CAP_PROP_POS_MSEC)/1000.0
        print(f"[ALERT] motion START at {ts(t_start)}"); last_alert = now()
    if not moving and motion_on:
        t_end = cap.get(cv2.CAP_PROP_POS_MSEC)/1000.0
        print(f"[ALERT] motion END   at {ts(t_end)}  (dur {ts(t_end - t_start)})")
        motion_on = False

    # Optional preview
    # cv2.imshow("frame", frame); cv2.imshow("mask", mask)
    # if (cv2.waitKey(1) & 0xFF) == 27: break

cap.release()
# cv2.destroyAllWindows()




