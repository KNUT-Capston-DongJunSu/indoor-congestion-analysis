import os
import threading
from django.apps import AppConfig

class VideostreamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.videostream'

    predictor = None
    background_thread = None
    stop_background = False
    
    def ready(self):
        """앱 시작 시 실행"""
        if os.environ.get('RUN_MAIN') == 'true':
            print("🚀 예측 시스템 초기화 중...")
            from .analytics.prediction_system import RealtimeCongestionPredictor
            VideostreamConfig.predictor = RealtimeCongestionPredictor()
