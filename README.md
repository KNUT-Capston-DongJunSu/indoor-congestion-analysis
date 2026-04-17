# AnEmptySeat (빈자리)

실내 공간의 **실시간 혼잡도를 감지하고 예측**하는 웹 애플리케이션입니다.
카페, 공연장, 마트 등 영상 스트림을 분석하여 현재 혼잡도와 미래 혼잡도를 대시보드로 제공합니다.

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Django 5.2, Python 3.10 |
| 객체 감지 | YOLOv8 (Ultralytics) |
| 객체 추적 | OCSort |
| 혼잡도 예측 | RandomForest (scikit-learn) |
| 프론트엔드 | HTML / CSS / JavaScript |
| 배포 | Gunicorn + Nginx (AWS EC2) |

---

## 프로젝트 구조

```
AnEmptySeat/
├── backend/          # Django 백엔드 (API, YOLO 추론, 혼잡도 분석)
├── frontend/         # 웹 UI (HTML, CSS, JS)
├── models/           # 사전 학습된 ML 모델 (.pt, .pkl)
├── docs/             # 문서
├── manage.py         # Django 진입점
├── requirements.txt  # Python 의존성
└── .env              # 환경 변수 (SECRET_KEY)
```

---

## 주요 URL

| URL | 설명 |
|-----|------|
| `/` | 메인 대시보드 |
| `/stream/<영상명>/` | 실시간 스트림 |
| `/stream/api/predictions/` | 혼잡도 예측 API |

---

## 보조 스크립트

```bash
python calibrate.py      # 혼잡도 임계값 캘리브레이션
python generate_data.py  # 학습 데이터 생성
python generate_video.py # 테스트 영상 생성
python train_model.py    # 예측 모델 재학습
```

---

## 실행 방법

환경 설정 및 실행 방법은 [docs/how_to_run.md](docs/how_to_run.md) 를 참고하세요.
