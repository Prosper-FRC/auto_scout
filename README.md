# auto_scout

Auto Scouting
A 6 week preseason project 
Breakdown of how it can work
1) Get field geometry
Extract frame from video.
Annotate known field corners/lines → compute homography to map pixels → field coordinates.
2) Detect robots
Train or fine-tune an object detector (YOLO, RT-DETR) for FRC robots.
Use color filters to split red vs blue bumpers.
OCR to read team numbers on bumpers (cache ID once it’s clear).
3) Track movement
Use multi-object tracking (e.g., ByteTrack, OC-SORT).
Apply homography to map detections into X,Y on field.
Generate path traces per robot.
4) Detect scoring
Define polygons for goals/score zones in field coordinates.
Track when a robot delivers a game piece into those zones.
For piece scoring, detect game pieces entering zones and disappearing or slowing to zero velocity.
Count events, time-stamp them, attribute to nearest robot.
5) Output
For each team: path, number of scores, where they scored, cycle times.
Format: CSV, JSON, or direct integration into FRC scouting databases.
Feasible workflow
Download video with yt-dlp.
Run detector+tracker pipeline on frames.
Map results to field coordinates.
Count and summarize events.



Simple Test For an Early Win
Build a simple motion-change alert first. CPU-only.
What it does
Reads a video.
Builds a background model.
Triggers an alert when pixels change above a threshold.
Logs start/stop times of motion.
Install:

python -m venv .venv && source .venv/bin/activate
pip install opencv-python numpy

Script:
Motion_alert.py


import cv2, numpy as np, time

VIDEO = "input.mp4"    # or 0 for webcam
MIN_AREA = 1500        # pixels; tune per resolution
COOLDOWN = 0.4         # seconds between alerts

cap = cv2.VideoCapture(VIDEO)
fg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
last_alert = 0
motion_on = False
t_start = None

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





Build Plan
Phase 1 — Core Reef Tracking
1) Data Ingest
Build: video fetch + decode to frames.
With: yt-dlp, ffmpeg-python, OpenCV (cv2.VideoCapture), Python 3.10+.
2) Field Calibration
Build: homography tool to click 6–12 field points → save H. **H**
With: OpenCV (findHomography, perspectiveTransform), a small Tk/Qt or CLI tool, JSON for points.
3) Detection
Build: models for robots (bumpers) and coral.
With: PyTorch + Ultralytics YOLO/RT-DETR; Label Studio/CVAT for annotation; ONNX export for speed.
4) Tracking + ID
Build: multi-object tracking per frame, alliance color split, optional OCR for team numbers.
With: OC-SORT/ByteTrack (Python), OpenCV color masks, PaddleOCR/TrOCR for bumper numbers.
5) Coordinate Mapping
Build: pixel → field XY projector using saved H.
With: OpenCV perspectiveTransform; simple data class for poses.
6) Reef Scoring Logic
Build: polygons for 6 faces × L1–L4; event detector that latches a coral “placement.”
With: Shapely or custom point-in-polygon; hysteresis over N frames; JSON for zone polygons.
7) Attribution
Build: possession heuristic and nearest-robot match in prior Δt window.
With: simple FSM + KDTree (scikit-learn) on recent robot XY.
8) Outputs
Build: event ledger and per-team summary.
With: SQLite/Postgres + SQLAlchemy or SQLite + raw SQL; CSV/JSON export.
9) Minimal UI
Build: overlay + table of events.
With: FastAPI + small React/Vite page or pure FastAPI templates; WebSocket for live.

Phase 2 — Add Extra Scoring (Processor/Net/Barge/Algae)
Zones
Build: new polygons and labels in the same JSON.
With: same Shapely/point-in-polygon.
Detectors
Build: add “algae” class; retrain.
With: same YOLO pipeline; augment data.
Events
Build: entry/exit rules per zone; dedupe and confidence scoring.
With: shared event engine; per-zone thresholds in JSON.
Human Overrides (optional)
Build: tablet page with accept/reject and manual add.
With: FastAPI endpoints + simple HTML buttons.

Phase 3 — Future Game Generalization
Rules Layer
Build: versioned rules.json schema: pieces, zones, points, latch windows, alliance constraints, phase timings.
With: JSON Schema for validation; semver tags.
Season Swap
Build: config loader that hot-swaps rules and zone files.
With: environment var or CLI --rules path/to/rules.json.
Retrain Pipeline
Build: reproducible training scripts and datasets per piece type.
With: poetry/conda, dvc or git-lfs for data, YOLO training scripts.
Calibration Refresh
Build: per-event calibration wizard.
With: same homography tool; store H per camera per event.

Phase 4 — System Architecture
Services
Build: modular processes: ingest → detect/track → project → events → store → API/UI.
With: Python processes; multiprocessing or lightweight queues (redis, zeromq).
APIs
Build: REST for queries, WebSocket for live events.
With: FastAPI, Pydantic models.
Storage
Build: append-only ledger + aggregates.
With: SQLite for local, Postgres for team use; nightly JSON/CSV export.
Monitoring
Build: health pings, FPS, dropped frames, OCR hit rate.
With: Prometheus client + Grafana (optional) or simple logs + status page.
Packaging
Build: reproducible env + CLI.
With: poetry, pip-tools, Dockerfile (CPU and CUDA variants).

Deliverables checklist (minimal viable)
calibrate.py (click points → H.json)
rules.json (zones, pieces, points)
detect_track.py (YOLO + ByteTrack → tracks.jsonl)
events.py (reef logic → events.jsonl / DB)
summarize.py (per-team CSV)
api.py (FastAPI) + ui/ (overlay + table)
train/ (labels, scripts, README)

Update flow each season
Record a clean field frame. Run calibrate.py → new H.json.
Define new zones in rules.json.
Collect 2–3k labels for new pieces. Retrain detector. Export ONNX.
Drop files into models/ and configs/. Restart services. Done.




Open-source Tools
Core stack (free)
Video I/O: ffmpeg, yt-dlp, opencv-python
ML runtime: pytorch (CPU or CUDA) or onnxruntime (fast CPU), numpy
Detection: Ultralytics YOLO (AGPL but free) or export to ONNX
Tracking: bytetrack-pytorch or ocsort
OCR (team numbers): paddleocr (easy) or tesseract-ocr + pytesseract
Geometry: shapely, scikit-learn (KDTree), scipy
Field calib: OpenCV homography tools you write; store JSON
Rules/Events: your Python module reading rules.json
Storage/Exports: sqlite3 (builtin) or postgres + psycopg, CSV/JSON
API/UI: fastapi, uvicorn, tiny HTML/JS frontend (or plotly-dash if preferred)
Labeling: Label Studio or CVAT (both free, self-hostable)
Nice-to-have (free)
Packaging: poetry or pip-tools
Data/versioning: git-lfs, dvc
Monitoring: prometheus_client; Grafana (optional)
Containers: Docker (optional), CUDA images if you have NVIDIA
Mapping tasks → tools
Download and decode video: yt-dlp, ffmpeg-python or OpenCV
Calibrate field: OpenCV (findHomography, perspectiveTransform), save H.json
Detect robots/coral: Ultralytics YOLO → export .onnx for onnxruntime if CPU-only
Track objects: ByteTrack/OC-SORT on detections
Alliance color + OCR: HSV masks for red/blue; paddleocr to read bumpers once per robot
Project to field XY: OpenCV + your saved H
Scoring events: shapely point-in-polygon + hysteresis; rules from rules.json
Attribution: nearest robot in Δt window using sklearn.neighbors.KDTree
Persist and summarize: SQLite tables for tracks, events; CSV/JSON exports
Serve results: fastapi REST + WebSocket; simple HTML overlay




Week-by-week (MVP to reef scoring)
Setup: Git repo, Python env, ffmpeg/OpenCV, sample VODs. Read rules. Pick roles.
Calibration tool: click field points → save H.json. Verify pixel→field warp.
Detection baseline: YOLO pretrained, run on frames, dump boxes. Label 300–500 frames.
Tracking: ByteTrack/OC-SORT. Persist tracks.jsonl. Simple path visualizer.
Alliance/ID: bumper color mask. Optional OCR spike. Pick nearest-robot ID strategy.
Reef zones: encode L1–L4 polygons. Scoring latch logic with hysteresis. Event ledger.
Evaluation: hand-score 2–3 matches. Compare precision/recall. Fix obvious misses.
Export/UI: per-team CSV, tiny FastAPI page with overlay. Basic docs and demo.
Hardening and extra scoring (optional, +6–8 weeks)
New detectors: add coral/algae classes; collect 1–2k labels; retrain; ONNX export.
Processor/Net/Barge logic: add polygons and zone rules to same engine.
Attribution tuning: possession window, KDTree nearest, tie-breaks, confidence.
Review tools: 10 s replay buffer, accept/reject, manual add event.
Packaging: Poetry, config files, CLI. SQLite schema, CSV/JSON nightly dump.
Benchmarking: FPS, accuracy across 10 matches. Writeup and maintenance guide.
Roles to parallelize
Vision model: 2 students (labels, training, eval).
Tracking + events: 2 students (fusion, rules).
Tools/UI: 1–2 students (calibration app, FastAPI, exports).
PM/QA: 1 student (ground-truthing, schedule, docs).
Key assumptions
GPU available. CPU-only adds 2–4 weeks.
Labeling time dominates; plan 5–8 hours just for labels.
Start with reef-only to hit MVP; add other zones later.
Update for next season
1–2 weeks: new calibration, update rules.json zones/points, collect 500–1000 labels for new pieces, quick retrain. Core pipeline stays the same.






Installs

python -m venv .venv && source .venv/bin/activate
pip install opencv-python onnxruntime ultralytics numpy scipy shapely scikit-learn fastapi uvicorn[standard] paddleocr ffmpeg-python
# system deps: ffmpeg, tesseract-ocr (if using pytesseract)




REPO Skeleton

configs/
  rules.reefscape.json
  camera_H.json
models/
  detector.onnx
src/
  calibrate.py
  detect_track.py
  project_xy.py
  events.py
  summarize.py
  api.py
ui/
  index.html  main.js
data/
  samples/
outputs/
  events.jsonl  per_team.csv  heatmaps/




Definitions

H:
In homogeneous coords: [u,v,1]T∼H [x,y,1]T[u,v,1]T∼H[x,y,1]T
[x,y][x,y] = image pixel; [u,v][u,v] = field-plane coords (e.g., meters).
“∼∼” means equal up to a scale; you divide by the third component after multiply.
Properties:
Projective transform (8 DoF). Assumes all mapped points lie on one plane.
Needs ≥4 non-collinear point pairs; 6–12 improves robustness.
Degenerate if points are collinear or nearly so.
Compute (OpenCV):
H, mask = cv2.findHomography(img_pts, field_pts, method=cv2.RANSAC)
# Map pixels -> field
p = np.hstack([pixels, np.ones((len(pixels),1))])      # Nx3
q = (H @ p.T).T
field_xy = q[:, :2] / q[:, 2:3]

Use:
Click 6–12 recognizable field features in the frame → img_pts.
Enter their known field coordinates (meters) → field_pts.
Save H and reuse to convert tracked pixel paths to field XY.

