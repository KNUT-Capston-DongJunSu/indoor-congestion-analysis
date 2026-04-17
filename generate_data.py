import json
import cv2
import os
from datetime import datetime, timedelta

# (필요한 import 경로)
from backend.videostream.ml.yolo_manager import YoloManager
from backend.config.settings import YOLO_MODEL_NAME
from backend.videostream.manager.video_manager import BaseVideoCap
from backend.videostream.analytics.occupancy import calc_spatial_density
from backend.videostream.analytics.calc_congestion import CongestionCalculator

def load_calibration_config(config_file='calibration_thresholds.json'):
    """저장된 임계값 설정을 불러옵니다."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            print(f"📊 임계값 로드 성공: {config_file}")
            return config['T1'], config['T2'], config['T3']
    except FileNotFoundError:
        print(f"🚨 [오류] 임계값 파일({config_file})을 찾을 수 없습니다.")
        print("먼저 calibrate.py를 실행하여 보정을 완료하세요.")
        return None, None, None
    except KeyError:
        print(f"🚨 [오류] 임계값 파일 형식이 잘못되었습니다.")
        return None, None, None

def generate_data_from_video(video_path, thresholds, output_file='training_data.json'):
    """
    (수정됨) 실제 영상에서 정확히 1초 간격으로 (count, level) 학습 데이터를 수집합니다.
    """
    print(f"📹 [2단계] 학습 데이터 생성 시작: {video_path}")
    
    t1, t2, t3 = thresholds
    yolo_manager = YoloManager(YOLO_MODEL_NAME)
    
    congestion_calc = CongestionCalculator(
        T1_NORMAL=t1, 
        T2_CROWDED=t2, 
        T3_CONGESTED=t3
    )

    manager = BaseVideoCap()
    cap, *_ = manager.init_cap(video_path)

    if not cap.isOpened():
        print(f"🚨 [오류] 비디오를 열 수 없습니다: {video_path}")
        return []

    # --- 1. FPS 기반 프레임 건너뛰기 설정 ---
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(fps)
    if fps == 0:
        print("⚠️ [경고] 비디오 FPS를 읽을 수 없습니다. 기본값 30으로 설정합니다.")
        fps = 30
    
    # 1초마다 1개의 프레임을 처리하기 위해 건너뛸 프레임 수 계산
    frames_to_skip = int(round(fps))
    print(f"   ... 비디오 FPS: {fps:.2f}, {frames_to_skip} 프레임마다 1개씩 처리 (약 1초 간격)")

    collected_data = []
    frame_count = 0
    
    # --- 2. 실제 시간 대신 사용할 가상 시계 ---
    simulated_timestamp = datetime.now()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 정확히 `frames_to_skip` 만큼 건너뛰었을 때만 처리
        if frame_count % frames_to_skip == 0:
            results = yolo_manager.smart_predict_yolo(frame)
            count = len(results)
            occupancy = calc_spatial_density(results)
            level, label = congestion_calc.calculate_level(occupancy, count)
            
            data_point = {
                # --- 3. 가상 시계로 타임스탬프 기록 ---
                'timestamp': simulated_timestamp.isoformat(),
                'count': count,
                'level': level,
                'frame': frame_count
            }
            
            collected_data.append(data_point)
            print(f"   ... 데이터 수집 중 (프레임 {frame_count}): {count}명, 레벨 {level} ({label})")

            # --- 4. 가상 시계를 정확히 1초 증가 ---
            simulated_timestamp += timedelta(seconds=1)
        
        frame_count += 1
    
    cap.release()
    
    # JSON 저장
    with open(output_file, 'w') as f:
        json.dump(collected_data, f, indent=2)
    
    print(f"✅ 데이터 생성 완료: {len(collected_data)}개 포인트 → {output_file}")
    return collected_data

if __name__ == "__main__":
    # 1. 임계값 로드
    thresholds = load_calibration_config('calibration_thresholds.json')
    
    if all(thresholds): # T1, T2, T3가 모두 None이 아니면
        VIDEO_FILE_PATH = "./frontend/static/video/supermaket.mp4"

        # skip_frames 인자 제거 (함수 내부에서 자동으로 계산)
        generate_data_from_video(VIDEO_FILE_PATH, thresholds, output_file='training_data.json')
