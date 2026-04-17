import threading
from .video_processor import VideoProcessor 
from ..ml.yolo_manager import YOLO_MODEL
from typing import Dict, Optional

class StreamManager:
    def __init__(self):
        self.processors: Dict[str, Optional[VideoProcessor]] = {}
        self.lock = threading.Lock()

    def start_processor_if_not_running(self, file_name):
        with self.lock:
            if file_name in self.processors and self.processors[file_name].is_alive():
                # 이미 실행 중이면 아무것도 하지 않음
                return

            print(f"Creating new processor for {file_name}")

            processor = VideoProcessor(
                file_name=file_name,
                model=YOLO_MODEL
            )
            processor.start()

            self.processors[file_name] = processor

    def stop_processor(self, file_name):
        """특정 비디오 프로세서를 중지"""
        with self.lock:
            if file_name not in self.processors:
                print(f"No processor found for {file_name}")
                return False

            processor = self.processors[file_name]
            
            if not processor.is_alive():
                print(f"Processor for {file_name} is already stopped")
                del self.processors[file_name]
                return True

            print(f"Stopping processor for {file_name}")
            
            # VideoProcessor에 stop 메서드가 있다고 가정
            processor.stop()
            
            # 스레드가 종료될 때까지 대기 (최대 5초)
            processor.join(timeout=5)
            
            if processor.is_alive():
                print(f"Warning: Processor for {file_name} did not stop gracefully")
            else:
                print(f"Processor for {file_name} stopped successfully")
            
            # 딕셔너리에서 제거
            del self.processors[file_name]
            return True

    def stop_all_processors(self):
        """모든 비디오 프로세서를 중지"""
        with self.lock:
            file_names = list(self.processors.keys())
        
        for file_name in file_names:
            self.stop_processor(file_name)
        
        print("All processors stopped")

    def get_active_processors(self):
        """현재 실행 중인 프로세서 목록 반환"""
        with self.lock:
            return [name for name, proc in self.processors.items() if proc.is_alive()]


# 애플리케이션 전체에서 사용할 단일 인스턴스
stream_manager = StreamManager()