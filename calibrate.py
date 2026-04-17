import os
import cv2
import json
from backend.videostream.ml.yolo_manager import YoloManager
from backend.videostream.analytics.occupancy import calc_spatial_density
from backend.videostream.analytics.calc_congestion import CongestionCalculator
from backend.config.settings import YOLO_MODEL_NAME

# (YoloManager, CongestionCalculator 등 다른 클래스/함수 정의는 여기에 있다고 가정합니다)


def run_calibration_from_video(video_path, percentile_config=(70, 85, 95)):
    """
    (수정됨) 동영상 파일을 분석하여 혼잡도 임계값을 계산합니다.
    """
    print(f"📊 [1단계] 임계값 보정 시작 (동영상): {video_path}")
    
    yolo_manager = YoloManager(YOLO_MODEL_NAME)
    congestion_calc = CongestionCalculator()
    
    # 동영상 파일 열기
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"🚨 [오류] 동영상 파일을 열 수 없습니다: {video_path}")
        return None

    congestion_calc.start_calibration()
    frame_count = 0
    
    # 동영상의 모든 프레임을 순회
    while cap.isOpened():
        ret, frame = cap.read()
        
        # ret이 False이면 비디오의 끝이거나 오류
        if not ret:
            print("\n... 동영상 처리 완료 ...")
            break

        # YOLO 예측 및 밀도 계산 (기존 로직과 동일)
        results = yolo_manager.smart_predict_yolo(frame) 
        count = len(results)
        occupancy = calc_spatial_density(results) 
        level, label = congestion_calc.calculate_level(occupancy, count)
        
        if label == "보정 중":
            # 10프레임마다 한 번씩만 로그를 출력하여 터미널이 너무 지저분해지는 것을 방지
            if frame_count % 10 == 0:
                print(f"   ... 보정 데이터 수집 중: 프레임 #{frame_count} ({count}명)")
        
        frame_count += 1
    
    # 비디오 객체 해제
    cap.release()
    
    # 보정 완료 및 결과 저장 (기존 로직과 동일)
    thresholds = congestion_calc.finish_calibration(percentiles=percentile_config)
    
    if thresholds:
        output_file = 'calibration_thresholds.json'
        with open(output_file, 'w') as f:
            # numpy float를 python float로 변환
            python_thresholds = {key: float(value) for key, value in thresholds.items()}
            json.dump(python_thresholds, f, indent=2)
        print(f"\n✅ 보정 완료! 임계값이 {output_file} 파일에 저장되었습니다.")
        print(thresholds)
    else:
        print("\n 보정 실패. 동영상에서 데이터를 수집하지 못했습니다.")

if __name__ == "__main__":
    # 1. '덜 붐빔', '보통', '매우 붐빔' 장면이 섞인 동영상 파일 경로
    CALIBRATION_VIDEO_FILE = "frontend/static/video/supermaket.mp4" # 👈 여기에 실제 동영상 파일 경로를 입력하세요.
    
    # 2. 보정 실행 (T1=25%, T2=50%, T3=75% 지점의 값으로 임계값 설정)
    run_calibration_from_video(CALIBRATION_VIDEO_FILE, percentile_config=(25, 50, 75))
