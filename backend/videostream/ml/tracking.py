import numpy as np
from collections import deque

def filter_tracks_by_class(track_hist, tracks):
    # tracks: 리스트 of [x1, y1, x2, y2, id]
    filtered_ids = []

    for obj in tracks:
        x1, y1, x2, y2, track_id, *rest = obj
        bbox = [x1, y1, x2, y2]

        # 기록 저장
        if track_id not in track_hist:
            track_hist[track_id] = deque(maxlen=10)
        track_hist[track_id].append(bbox)

        # 이동 거리 계산
        if len(track_hist[track_id]) >= 2:
            dist_sum = 0
            boxes = list(track_hist[track_id])
            for i in range(len(boxes)-1):
                cx1 = (boxes[i][0] + boxes[i][2]) / 2
                cy1 = (boxes[i][1] + boxes[i][3]) / 2
                cx2 = (boxes[i+1][0] + boxes[i+1][2]) / 2
                cy2 = (boxes[i+1][1] + boxes[i+1][3]) / 2
                dist = ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5
                dist_sum += dist
            avg_dist = dist_sum / (len(boxes)-1)
        else:
            avg_dist = 0

        if avg_dist > 0.1:
            filtered_ids.append(track_id)
        else:
            pass  # 오탐 제거 또는 무시

    return np.array(filtered_ids).astype(int)


def tracking_object(tracker, tracker_input, frame_id):
    if len(tracker_input) == 0:
        return []
    else: 
        return tracker.update(tracker_input, frame_id)
    
    
def tracking_object_filtered(tracker, tracker_input, frame_id):
    if len(tracker_input) == 0:
        tracked_objects = []  # 또는 빈 텐서 등, 트래커가 처리할 수 없는 빈 입력에 대비
    else:
        tracked_objects = tracker.update(tracker_input, frame_id)
        filtered_ids = filter_tracks_by_class(tracked_objects)
        if len(filtered_ids) != 0:
            tracked_ids = tracked_objects[:, 4].astype(int)
            indices = np.where(np.isin(tracked_ids, filtered_ids))[0]
            tracked_objects = tracked_objects[indices] 

    return tracked_objects

