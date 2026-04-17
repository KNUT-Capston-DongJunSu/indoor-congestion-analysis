import json
import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# --- 1. 학습 설정 (1초 데이터용으로 수정) ---

# 1-1. X (입력): 과거 30초(30개)의 데이터를 본다.
LOOKBACK_WINDOW = 100

# 1-2. y (정답): 미래 10초, 20초, 30초 뒤를 예측한다.
PREDICTION_HORIZONS = [10, 20, 30]

# 1-3. 파일 경로
TRAINING_DATA_FILE = 'training_data.json'
MODEL_OUTPUT_PATH = 'models/congestion_predictor_model_v2.pkl'

# --- 2. 시계열 데이터셋 생성 함수 ---

def create_timeseries_dataset(data, lookback_window, horizons):
    """
    (X, y) 시계열 데이터셋을 생성합니다.
    
    (수정됨) 가정: 'data' 리스트는 1초 간격으로 정렬되어 있음
    
    (수정됨) 예시: lookback=60, horizons=[30, 60, 120]
    - X: [count(t-60), level(t-60), ..., count(t-1), level(t-1)] (과거 60초)
    - y: [level(t+30), level(t+60), level(t+120)] (미래 30초, 60초, 120초 뒤)
    """
    X, y = [], []
    max_horizon = max(horizons)
    
    for i in range(lookback_window, len(data) - max_horizon):
        
        # 1. X 생성
        x_window = data[i - lookback_window : i]
        x_features = []
        for point in x_window:
            x_features.append(point['count'])
            x_features.append(point['level'])
        
        # 2. y 생성
        y_targets = []
        for h in horizons:
            # (i + h - 1) 인덱스의 level 값
            y_targets.append(data[i + h - 1]['level'])
            
        X.append(x_features)
        y.append(y_targets)
        
    return np.array(X), np.array(y)

# --- 3. 메인 학습 로직 ---

def train_new_model():
    print(f"🎓 [V2 모델] 학습 시작: {TRAINING_DATA_FILE}")

    # 데이터 로드
    try:
        with open(TRAINING_DATA_FILE, 'r') as f:
            data = json.load(f)
            
    except FileNotFoundError:
        print(f"🚨 [오류] 학습 데이터 파일({TRAINING_DATA_FILE})을 찾을 수 없습니다.")
        return
    
    if len(data) < LOOKBACK_WINDOW + max(PREDICTION_HORIZONS):
        print(f"🚨 [오류] 데이터가 너무 적습니다. 최소 {LOOKBACK_WINDOW + max(PREDICTION_HORIZONS)}개 필요합니다.")
        return

    # 1. 시계열 데이터셋 생성
    print(" ... 시계열 데이터셋(X, y) 생성 중...")
    X, y = create_timeseries_dataset(data, LOOKBACK_WINDOW, PREDICTION_HORIZONS)
    
    if len(X) == 0:
        print("🚨 [오류] (X, y) 쌍을 만들 수 없습니다. 데이터가 부족합니다.")
        return
        
    print(f" ... 총 {len(X)}개의 (X, y) 학습 세트 생성 완료.")
    
    # 2. 훈련 / 테스트 데이터 분리
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    # 3. 모델 정의
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('forest', RandomForestRegressor(
            n_estimators=100, 
            random_state=42,
            n_jobs=-1,         
            max_depth=10       
        ))
    ])
    
    # 4. 모델 학습
    print(" ... 모델 학습 중 ...")
    model.fit(X_train, y_train)
    
    # 5. 모델 성능 평가
    score = model.score(X_test, y_test)
    print(f" ... 모델 학습 완료! (Test Score: {score*100:.2f}%)")
    
    # 6. 모델 저장
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    model_data = {
        'model': model,
        'lookback_window': LOOKBACK_WINDOW,
        'horizons': PREDICTION_HORIZONS
    }
    with open(MODEL_OUTPUT_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"✅ 예측 모델 학습 완료! 모델 저장: {MODEL_OUTPUT_PATH}")

    # 7. 예측 테스트
    print("\n🔮 예측 테스트 (예시):")
    print(f"   (테스트 데이터 마지막 {LOOKBACK_WINDOW}개(초) 사용)") 
    
    X_sample = X_test[-1:] 
    y_true = y_test[-1]
    y_pred = model.predict(X_sample)[0]
    
    print(f"   - 실제 정답 (y_true): {np.round(y_true, 1)}")
    print(f"   - 모델 예측 (y_pred): {np.round(y_pred, 1)}")
    
    print("\n   [예측 결과 해석]")
    
    for i, seconds_ahead in enumerate(PREDICTION_HORIZONS):
        print(f"   - {seconds_ahead}초 후: (실제 {y_true[i]}) -> (예측 {y_pred[i]:.1f})")


if __name__ == "__main__":
    train_new_model()
    # from backend.config.settings import REGRESSION_MODEL_NAME, MODEL_DIR
    # with open(f'{MODEL_DIR}/{REGRESSION_MODEL_NAME}', 'rb') as f:
    #     model_data = pickle.load(f)
    # print(model_data)