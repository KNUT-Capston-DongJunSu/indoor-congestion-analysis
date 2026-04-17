import os, cv2, time, threading
from collections import deque 
from django.core.cache import cache
from backend.config.settings import VIDEO_DIR

from ocsort import OCSort
from ..apps import VideostreamConfig
from .video_manager import BaseVideoStreamer
from ..analytics.occupancy import calc_spatial_density
from ..analytics.calc_congestion import CongestionCalculator
from ..ml.tracking import tracking_object
from ..ml.postprocessing import draw_tracking_boxes

class VideoProcessor(threading.Thread):
    """
    하나의 비디오 스트림을 독립적으로 처리하는 스레드 클래스입니다.
    각 인스턴스는 고유한 캐시 키를 사용하여 다른 스트림과 데이터가 섞이지 않도록 합니다.
    """
    def __init__(self, file_name, model):
        super().__init__()
        self.daemon = True  # 메인 스레드 종료 시 함께 종료
        self.running = True  # 중지 플래그 추가
        self.history_lock = threading.Lock()  # history 데이터 업데이트 시 경쟁 조건 방지를 위한 락

        self.yolo_model = model
        self.congestion_calc = CongestionCalculator()
        self.tracker = OCSort(det_thresh=0.3, max_age=50, min_hits=1)

        video_path = os.path.join(VIDEO_DIR, file_name)
        self.streamer = BaseVideoStreamer(video_path, True, file_name)
        self.file_name = file_name
        self.frame_cache_key = f'{self.file_name}_latest_frame_bytes'
        self.status_cache_key = f'{self.file_name}_current_congestion_status'
        self.history_cache_key = f'{self.file_name}_congestion_history'

    def stop(self):
        """프로세서 중지 플래그 설정"""
        self.running = False

    def run(self):
        """스레드가 시작되면 실행되는 메인 영상 처리 루프입니다."""
        last_update_time = 0
        frame_id = 0

        while self.running and self.streamer.cap.isOpened():
            ret, frame = self.streamer.cap.read()
            frame_id += 1
            # if frame_id % 13 != 0:
            #     continue
            
            if not ret:
                # 영상의 마지막 프레임에 도달 - 루프 반복 대신 종료 처리
                # 종료 신호를 캐시에 저장하여 frame_generator가 스트리밍을 중단할 수 있도록 함
                cache.set(f'{self.file_name}_video_finished', True, timeout=60)
                self.running = False
                break

            # --- 딥러닝 및 혼잡도 계산 로직 ---
            results = self.yolo_model.smart_predict_yolo(frame=frame, conf=0.07)
            tracked_objects = tracking_object(self.tracker, results, self.streamer.frame_id)
            object_count = len(tracked_objects)

            occupancy = calc_spatial_density(tracked_objects)
            level, label = self.congestion_calc.calculate_level(occupancy, object_count)
            
            print(f"[{self.file_name}] Occupancy: {occupancy:.2f}, Label: {label}")
            plot = draw_tracking_boxes(frame, tracked_objects, label)
            
            # 처리된 프레임을 결과 영상 파일에 저장
            if self.streamer.save_enabled:
                self.streamer.video_writer.write(plot)

            # JPEG 이미지로 인코딩
            ret, buffer = cv2.imencode('.jpg', plot)
            if ret:
                frame_bytes = buffer.tobytes()
                # 처리된 최종 프레임을 고유 캐시 키에 저장
                cache.set(self.frame_cache_key, frame_bytes, timeout=5)

            # 혼잡도 데이터를 고유 캐시 키에 저장
            congestion_data = {"level": level, "label": label, "occupancy": occupancy, "object_count": object_count}
            cache.set(self.status_cache_key, congestion_data, timeout=10)
            self.perform_data_collection_once(congestion_data)
            
            # --- 시간별 데이터 누적 저장 ---
            current_time = time.time()
            if current_time - last_update_time >= 1: # 1초마다 업데이트
                last_update_time = current_time
                
                # 3. Lock을 사용한 경쟁 조건 방지
                with self.history_lock:
                    history = cache.get(self.history_cache_key, deque(maxlen=30))
                    history.append((time.strftime('%H:%M:%S'), occupancy))
                    cache.set(self.history_cache_key, history, timeout=3600)

        self.streamer.cap.release()

        # 영상 저장이 활성화된 경우, 모든 프레임 쓰기가 끝난 후 파일을 닫아 저장 완료
        if self.streamer.save_enabled:
            self.streamer.video_writer.close_writer()
            print(f"[{self.file_name}] 결과 영상 저장 완료: {self.streamer.output_dir}{self.file_name}")

    def perform_data_collection_once(self, status):
        predictor = VideostreamConfig.predictor
        if not predictor:
            print("Data collection failed: Predictor not initialized.")
            return None
        
        try:
            if status:
                # 2. Predictor에 데이터 추가
                predictor.add_data(
                    count=status.get('object_count', 0),
                    level=status.get('level', 3)
                )
                return status
            else:
                print("Data collection failed: No status returned.")
                return None
        except Exception as e:
            print(f"Data collection exception: {e}")
            return None