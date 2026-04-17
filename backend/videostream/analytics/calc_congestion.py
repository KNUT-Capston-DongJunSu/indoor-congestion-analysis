import numpy as np
# (calc_spatial_density 함수는 동일)

class CongestionCalculator:
    
    def __init__(self, history_len=30, T1_NORMAL=10.0, T2_CROWDED=20.0, T3_CONGESTED=35.0):     
        self.history_len = history_len  # 스무딩을 위한 윈도우
        self.history = []               # 최근 N프레임 점수 (스무딩용)
        
        # 1. 보정(Calibration) 관련 변수
        self.calibration_data = []      # 보정 시 데이터 수집용
        self.is_calibrating = False     # 현재 보정 모드인지 여부
        
        # 2. 임계값 (기본값 또는 보정 후 설정될 값)
        self.T1_NORMAL = T1_NORMAL
        self.T2_CROWDED = T2_CROWDED
        self.T3_CONGESTED = T3_CONGESTED

    # --- 보정(Calibration) 관련 함수 ---
    
    def start_calibration(self):
        """보정 모드를 시작합니다."""
        self.is_calibrating = True
        self.calibration_data = []
        print("[System] 보정 모드를 시작합니다. 데이터를 수집합니다...")

    def finish_calibration(self, percentiles=(70, 85, 95)):
        """
        수집된 데이터를 기반으로 임계값을 설정하고 보정 모드를 종료합니다.
        percentiles: (T1, T2, T3)에 해당하는 백분위수 튜플
        """
        if not self.calibration_data:
            print("[Warning] 수집된 데이터가 없어 보정을 완료할 수 없습니다.")
            self.is_calibrating = False
            return

        # numpy를 사용해 백분위수 계산
        p_t1, p_t2, p_t3 = percentiles
        self.T1_NORMAL = np.percentile(self.calibration_data, p_t1)
        self.T2_CROWDED = np.percentile(self.calibration_data, p_t2)
        self.T3_CONGESTED = np.percentile(self.calibration_data, p_t3)
        
        self.is_calibrating = False
        self.calibration_data = [] # 메모리 해제
        
        print(f"[System] 보정 완료! 총 {len(self.calibration_data)}개의 데이터 사용.")
        print(f"  - T1 (보통): {self.T1_NORMAL:.2f} ({p_t1}th percentile)")
        print(f"  - T2 (혼잡): {self.T2_CROWDED:.2f} ({p_t2}th percentile)")
        print(f"  - T3 (매우 혼잡): {self.T3_CONGESTED:.2f} ({p_t3}th percentile)")

        return {
            'T1': self.T1_NORMAL, 
            'T2': self.T2_CROWDED, 
            'T3': self.T3_CONGESTED
        }

    # --- 기존 계산 함수 (수정됨) ---

    def update_history(self, current_density_score):
        self.history.append(current_density_score)
        if len(self.history) > self.history_len:
            self.history.pop(0)
    
    def calculate_level(self, occupancy_score, num_objects):
    
        # 1인당 밀집도 점수 (scale / avg_dist)
        # (num_objects=1 일 경우 spatial_density가 0을 반환하므로 density_score는 0이 됨)
        density_score = 0.0
        if num_objects > 1:
            density_score = occupancy_score
        
        # 3. [수정] 보정 모드일 경우, 데이터만 수집
        if self.is_calibrating:
            if density_score > 0: # 의미 있는 데이터만 수집
                self.calibration_data.append(density_score)
            return 0, "보정 중" # 보정 중에는 '보정 중' 상태 반환
        
        # --- (운영 모드일 경우) ---
        
        self.update_history(density_score)
        
        non_zero_history = [s for s in self.history if s > 0]
        
        if not non_zero_history:
            smoothed_score = 0.0 # 최근 N프레임 동안 모두 0점이었음
        else:
            # 0이 아닌 값들의 평균을 계산 (보정 때와 동일한 기준)
            smoothed_score = sum(non_zero_history) / len(non_zero_history)
        
        # 절대 임계값과 비교
        if smoothed_score <= self.T1_NORMAL:
            return 1, "Normal"
        elif smoothed_score <= self.T2_CROWDED:
            return 2, "Common"
        elif smoothed_score <= self.T3_CONGESTED:
            return 3, "Crowded"
        else:
            return 4, "Very Crowded"