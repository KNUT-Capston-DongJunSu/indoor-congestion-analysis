# AnEmptySeat (빈자리)

**Real-time indoor space congestion detection and prediction web application.**

AnEmptySeat analyzes live video streams from cameras installed in cafes, restaurants, and other indoor spaces to estimate the current occupancy level and predict future congestion. Users can check real-time crowd status and recommended visit times through an intuitive web dashboard — without any dedicated hardware beyond a standard camera.

---

## Background & Motivation

Existing seat-management solutions such as POS-based systems or IoT sensor arrays require per-seat hardware installation, making them expensive to deploy and maintain. A single hardware failure can cascade into data inconsistencies, and the more sensors a system uses the higher its compounded failure probability becomes.

AnEmptySeat solves these problems with a **software-only approach**: a single camera feeds a deep-learning pipeline that detects and tracks people, computes a congestion score, and streams the results to a web dashboard — no per-seat hardware required.

---

## System Architecture

```
Camera / Video File
        │
        ▼
  ┌─────────────────────────────────────────────────┐
  │               Cloud Server (AWS EC2)            │
  │                                                 │
  │  YOLOv8m ──► OC-SORT ──► Line Density ──► DB   │
  │  Detection    Tracking    Algorithm      MySQL  │
  │                               │                 │
  │              Django REST API / WebSocket         │
  └───────────────────┬─────────────────────────────┘
                      │
                      ▼
             Web Browser Dashboard
         (real-time congestion + prediction)
```

### Processing Pipeline

1. **Video Input & Preprocessing** — Frames are captured from a webcam or video file via `cv2.VideoCapture`. Each frame is resized, normalized (0–1), converted from BGR to RGB, and converted to a PyTorch tensor before being passed to the model.

2. **Object Detection (YOLOv8m)** — A YOLOv8-Medium model pre-trained on the [Scut-Head](https://github.com/HCIILAB/SCUT-HEAD-Dataset-Release) dataset detects human heads in each frame. The model uses a Backbone → Neck → Head architecture and produces bounding boxes with confidence scores; overlapping boxes are filtered by NMS.

3. **Object Tracking (OC-SORT)** — Detected bounding boxes are fed into OC-SORT (Observation-Centric SORT), an improved multi-object tracker that applies observation-centric non-linear motion prediction instead of a plain Kalman filter. This keeps stable IDs across frames even during occlusion and prevents duplicate counting of the same person.

4. **Congestion Analysis — Line Density Algorithm** — Rather than computing a simple person-count-to-area ratio (which produces negligibly small values because frame resolution dominates the denominator), AnEmptySeat uses a novel **line density** metric:
   - Treat every detected object as a node.
   - Connect pairs of nodes that are within a configurable distance threshold with an edge.
   - The density of edges (lines) relative to the number of nodes reflects how tightly packed people are.
   - This density score is mapped to one of four congestion levels:

   | Level | Occupancy | Label |
   |-------|-----------|-------|
   | 1 | 0 – 30% | Relaxed (여유) |
   | 2 | 31 – 60% | Normal (보통) |
   | 3 | 61 – 90% | Congested (혼잡) |
   | 4 | 91%+ | Very Congested (매우 혼잡) |

5. **Congestion Prediction (RandomForest)** — A `RandomForestRegressor` (scikit-learn) is trained on simulated time-series data (hour-of-day, day-of-week, historical counts). Given the current time and live person count, the model predicts congestion levels for the next N minutes/hours and surfaces the best recommended visit time.

6. **Visualization & Storage** — Congestion level, object count, MJPEG video stream, and time-series prediction slots are served to the frontend and persisted in MySQL (Railway).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Object Detection | YOLOv8m (Ultralytics) + Scut-Head pretrained weights |
| Object Tracking | OC-SORT |
| Congestion Prediction | RandomForestRegressor (scikit-learn) |
| Backend | Django 5.2, Django REST Framework, Python 3.10 |
| Real-time Communication | WebSocket (Django Channels), MJPEG streaming |
| Frontend | Vanilla JavaScript, HTML5, CSS3 |
| Database | MySQL (Railway) |
| Deployment | Gunicorn + Nginx on AWS EC2 |
| Security | JWT authentication, OAuth2 |

---

## Project Structure

```
AnEmptySeat/
├── backend/
│   └── videostream/
│       ├── views.py              # ObjectDetector class, streaming & congestion API
│       ├── analytics/
│       │   ├── prediction_system.py   # PredictionModelV2: loads & runs RandomForest
│       │   ├── calc_spatial_density.py # Line density algorithm
│       │   └── congestion_calc.py     # CongestionCalculator: level classification
│       └── ml/
│           └── postprocessing/
│               └── draw_tracking_boxes.py
├── frontend/
│   └── static/
│       └── script.js             # Vanilla JS dashboard: fetch + setInterval polling
├── models/
│   ├── best_model.joblib         # Serialized RandomForest model
│   └── *.pt                      # YOLOv8 weights
├── docs/
│   └── how_to_run.md
├── calibrate.py                  # Congestion threshold calibration
├── generate_data.py              # Simulated training data generator
├── train_model.py                # Re-train the RandomForest prediction model
├── generate_video.py             # Test video generator
├── manage.py
└── requirements.txt
```

---

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/stream/<video_name>/` | GET | Live video stream page |
| `/stream/video_feed/` | GET | MJPEG stream (StreamingHttpResponse) |
| `/stream/status/<video_name>/` | GET | Current person count + congestion level (JSON, polled every 5 s) |
| `/stream/api/predictions/` | GET | Future congestion predictions (JSON, polled every 10 s) |

---

## Frontend Dashboard

The frontend is built with **Vanilla JavaScript** (no React/Vue) for minimal overhead:

- **`setupCongestionMonitor`** — polls `/stream/status/` every **5 seconds** via `fetch`, updates person count text and the visual congestion bar (`data-level` attribute).
- **`setupPredictionUI`** — polls `/stream/api/predictions/` every **10 seconds**, displays the recommended visit time and time-slot congestion forecast for the next hour.
- All DOM updates use `textContent` / `setAttribute` so the page never needs a full reload.

---

## Limitations & Future Work

| Area | Current Limitation | Planned Improvement |
|------|--------------------|---------------------|
| Prediction accuracy | Trained on simulated data; real-world variables (weather, holidays, events) are absent | Retrain on weeks of real in-store data |
| Occlusion handling | People obscured by furniture or each other can be missed | Switch to top-view camera angle; consider YOLOv8l |
| Scalability | MJPEG via `StreamingHttpResponse` is CPU/bandwidth-intensive under many concurrent viewers | Adopt Nginx RTMP / WebRTC / HLS-DASH for video delivery |
| Prediction model | RandomForest with hand-crafted features | Replace with LSTM for proper time-series modelling |
| Perspective distortion | Line-density uses 2D pixel coordinates, so depth distortion affects results | Apply homography correction for consistent real-world distances |

---

## Getting Started

See [docs/how_to_run.md](docs/how_to_run.md) for full setup and run instructions.

### Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Generate training data and retrain the prediction model
python generate_data.py
python train_model.py

# 3. (Optional) Calibrate congestion thresholds
python calibrate.py

# 4. Start the Django development server
python manage.py runserver
```

### Utility scripts

| Script | Purpose |
|--------|---------|
| `calibrate.py` | Compute optimal congestion thresholds from sample footage |
| `generate_data.py` | Generate simulated hour/day occupancy data for model training |
| `train_model.py` | Train and serialize the RandomForest prediction model |
| `generate_video.py` | Create synthetic test video clips |

---

## Acknowledgements

- [Ultralytics YOLOv8](https://docs.ultralytics.com/ko/models/yolov8/)
- [OC-SORT](https://arxiv.org/abs/2203.14360) — Observation-Centric SORT
- [Scut-Head Dataset](https://github.com/HCIILAB/SCUT-HEAD-Dataset-Release)
- Capstone Design 2025, Department of Electronic Engineering, KNUT
  - Advisor: Prof. Song Chang-ik
  - Team DongJunSu: Kim Dong-in (2222007), Kim Jun-hee (2122014)
