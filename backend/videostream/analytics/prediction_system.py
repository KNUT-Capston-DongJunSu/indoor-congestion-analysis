import os
import pickle
import numpy as np
from collections import deque
from datetime import datetime
from backend.config.settings import MODEL_DIR, REGRESSION_MODEL_NAME

class RealtimeCongestionPredictor:
    def __init__(self, model_name=REGRESSION_MODEL_NAME):
        """
        V2 모델(RandomForest)을 로드하여 실시간 예측을 수행합니다.
        """
        self.model = None
        self.lookback_window = 0
        self.horizons = []
        self.data_buffer = None
        model_path = os.path.join(MODEL_DIR, model_name)
        if not self.load_model(os.path.join(MODEL_DIR, model_name)):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")

    def load_model(self, model_path):
        """
        학습된 V2 모델(.pkl)을 로드합니다.
        """
        if not os.path.exists(model_path):
            print(f"🚨 [오류] 모델 파일이 없습니다: {model_path}")
            return False
            
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
            
        self.model = model_data['model']
        self.lookback_window = model_data['lookback_window']
        self.horizons = model_data['horizons']
        
        # 모델이 학습한 '과거' 만큼의 데이터만 저장하는 버퍼 생성
        self.data_buffer = deque(maxlen=self.lookback_window)
        
        print("✅ [V2 예측기] 모델 로드 완료!")
        print(f"   - Lookback Window: {self.lookback_window} 초")
        print(f"   - Prediction Horizons: {self.horizons} 초 뒤")
        return True

    def add_data(self, count, level):
        """
        (수정됨) 실시간 데이터를 버퍼에 추가합니다. (학습 X)
        """
        data_point = {
            'timestamp': datetime.now(),
            'count': count,
            'level': level
        }
        self.data_buffer.append(data_point)

    def _format_input_data(self):
        """
        (핵심) 버퍼의 데이터를 모델 입력 형식(1D-array)으로 변환합니다.
        train_model_v2.py의 create_timeseries_dataset 로직과 동일해야 합니다.
        """
        # 버퍼의 모든 데이터를 리스트로 변환 (순서 보장)
        current_data = list(self.data_buffer)
        
        x_features = []
        for point in current_data:
            x_features.append(point['count'])
            x_features.append(point['level'])
        
        # [count1, level1, count2, level2, ...] 형태의 1차원 배열
        return np.array(x_features)

    def predict(self):
        """
        (수정됨) 현재 버퍼 데이터를 기반으로 미래 혼잡도를 예측합니다.
        """
        
        # 1. 데이터가 충분히 모였는지 확인
        if len(self.data_buffer) < self.lookback_window:
            # 아직 데이터가 부족하면 '데이터 수집 중' 메시지 반환
            return [{
                'seconds_ahead': h,
                'level': 1,
                'label': '데이터 수집 중...'
            } for h in self.horizons]

        # 2. (핵심) 현재 버퍼로 예측용 X 샘플 1개 생성
        # X_sample은 [c1, l1, c2, l2, ..., c90, l90] 형태가 됨
        X_sample = self._format_input_data()
        
        try:
            # 3. 모델 예측
            # X_sample을 2D 배열로 만들어 (샘플 1개) 모델에 전달
            # predicted_levels 결과 예시: [4., 3., 2.]
            predicted_levels = self.model.predict([X_sample])[0]
            
            predictions = []
            
            # 4. 예측 결과를 JSON 형식으로 포맷팅
            for i, seconds in enumerate(self.horizons):
                level_raw = predicted_levels[i]
                level_int = int(round(level_raw))
                
                predictions.append({
                    'seconds_ahead': seconds,
                    'level': level_int,
                    'raw_level': float(level_raw),
                    'label': self._get_label(level_int)
                })
            
            return predictions
            
        except Exception as e:
            print(f"🚨 [V2 예측 오류] {e}")
            return [{
                'seconds_ahead': h,
                'level': 0,
                'label': '예측 오류'
            } for h in self.horizons]

    def _get_label(self, level):
        """레벨을 라벨로 변환"""
        labels = {1: '원활', 2: '보통', 3: '혼잡', 4: '매우 혼잡'}
        return labels.get(level, '보통')

# --- (참고) V2 예측기 사용 예시 ---
if __name__ == "__main__":
    # 1. V2 예측기 로드 (모델 파일을 자동으로 불러옴)
    try:
        predictor = RealtimeCongestionPredictor(
            model_path='models/congestion_predictor_model_v2.pkl'
        )
        
        # 2. 데이터가 아직 90초(lookback)만큼 안 모였을 때
        predictor.add_data(count=10, level=1) # 1초
        predictor.add_data(count=11, level=1) # 2초
        print("\n[테스트 1] 데이터 수집 중일 때:")
        print(predictor.predict())
        
        # 3. (가상) 90초 분량의 데이터를 채웠다고 가정
        for i in range(predictor.lookback_window):
             predictor.add_data(count=15 + (i//10), level=2)
             
        # 4. 90초가 찼을 때 예측
        print("\n[테스트 2] 데이터가 90개 찼을 때:")
        print(predictor.predict())
        
        # 5. 새로운 데이터가 1초 뒤에 들어옴 (버퍼는 자동으로 90개 유지)
        predictor.add_data(count=30, level=4)
        print("\n[테스트 3] 새로운 데이터 1개 추가 후 예측:")
        print(predictor.predict())

    except FileNotFoundError as e:
        print(e)
