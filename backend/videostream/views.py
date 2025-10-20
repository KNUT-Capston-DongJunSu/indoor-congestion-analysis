import time, io
import matplotlib; matplotlib.use('Agg')  # GUI 백엔드가 없는 환경에서 Matplotlib 사용 설정
import matplotlib.pyplot as plt

from django.http import JsonResponse
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.core.cache import cache

from .manager.stream_manager import stream_manager

def live_stream_view(request, file_name):
    """
    요청된 비디오의 처리 스레드를 실행(필요시)하고,
    캐시에서 프레임을 가져와 스트리밍하는 뷰.
    """
    # 👈 2. 이 뷰가 호출될 때, 해당 비디오 처리 스레드가 실행되도록 요청
    stream_manager.start_processor_if_not_running(file_name)

    # 👈 3. 기존의 프레임 생성 및 전송 로직은 그대로 유지
    def frame_generator():
        while True:
            # file_name을 사용하여 고유한 캐시 키를 조회
            cache_key = f'{file_name}_latest_frame_bytes'
            frame_bytes = cache.get(cache_key)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # CPU 부하를 줄이기 위한 지연
            time.sleep(0.03)

    return StreamingHttpResponse(
        frame_generator(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

def congestion_status(request, file_name):
    """현재 혼잡도 상태를 JSON으로 반환하는 API 뷰"""
    # ★★★ 전역 변수 대신 Django 캐시에서 상태 조회 ★★★
    stream_manager.start_processor_if_not_running(file_name)
    
    status = cache.get(f'{file_name}_current_congestion_status', {
        "level": 0,
        "label": "측정중",
        "occupancy": 0,
        "object_count": 0
    }) # 캐시에 값이 없으면 기본값 반환
    return JsonResponse(status)


def congestion_graph_view(request, file_name):
    """캐시에 저장된 데이터를 바탕으로 통일된 y축을 사용하는 그래프 이미지를 생성하여 반환"""
    stream_manager.start_processor_if_not_running(file_name)

    history = cache.get(f'{file_name}_congestion_history')

    if not history:
        return HttpResponse("아직 데이터가 수집되지 않았습니다.", status=204)

    timestamps, counts = zip(*history)

    # --- Matplotlib으로 그래프 생성 (수정된 버전) ---
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 1. 막대 그래프 (ax1에 그리기)
    ax1.bar(timestamps, counts, color='skyblue', label='Occupation')
    
    # 2. 꺾은선 그래프 (동일한 ax1에 그리기)
    ax1.plot(timestamps, counts, color='red', marker='o', linestyle='-', label='Trend')

    # Y축 라벨을 하나로 통합합니다.
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Occupation / Trend", color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.tick_params(axis='x', rotation=45)

    # 범례(legend)를 추가하여 두 그래프를 명확히 구분해 줍니다.
    ax1.legend()

    fig.suptitle('Time-based Congestion Rate')
    fig.tight_layout()

    # --- 그래프를 이미지 버퍼에 저장 ---
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    
    return HttpResponse(buf.getvalue(), content_type='image/png')