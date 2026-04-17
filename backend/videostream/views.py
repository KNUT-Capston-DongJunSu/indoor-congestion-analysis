import time, io, os
from datetime import datetime
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from functools import wraps

from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse

from .apps import VideostreamConfig # 상태 확인용
from .manager.stream_manager import stream_manager
from .analytics.prediction_system import RealtimeCongestionPredictor

def predictor_api_view(view_func):
    """
    Predictor API 뷰를 위한 데코레이터:
    1. Predictor 존재 여부 확인
    2. view_func에 'predictor' 객체를 인자로 전달
    3. 모든 예외를 처리하여 500 JsonResponse로 반환
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        predictor = VideostreamConfig.predictor
        if not predictor:
            return JsonResponse({
                'error': '예측 시스템이 초기화되지 않았습니다.'
            }, status=503)
        try:
            # 뷰 함수에 predictor를 키워드 인자로 전달
            return view_func(request, predictor=predictor, *args, **kwargs)
        except Exception as e:
            # 예외 발생 시 일관된 에러 응답 반환
            return JsonResponse({'error': str(e)}, status=500)
    return _wrapped_view

@require_http_methods(["GET"])
def live_stream_view(request, file_name):
    """요청된 비디오의 처리 스레드를 실행하고 프레임을 스트리밍합니다."""
    # 특정 비디오 프로세서 재시작 및 캐시 클리어
    stream_manager.stop_processor(file_name)
    cache.delete_many([
        f'{file_name}_latest_frame_bytes',
        f'{file_name}_current_congestion_status',
        f'{file_name}_congestion_history',
        f'{file_name}_video_finished',  # 이전 영상 종료 신호 초기화
    ])
    stream_manager.start_processor_if_not_running(file_name)

    def frame_generator():
        while True:
            frame_bytes = cache.get(f'{file_name}_latest_frame_bytes')
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # VideoProcessor가 영상 끝에서 설정한 종료 신호 확인
            # 신호가 있으면 제너레이터를 종료하여 HTTP 스트리밍 응답을 닫음
            if cache.get(f'{file_name}_video_finished'):
                break

            time.sleep(0.03) # CPU 부하 감소

    return StreamingHttpResponse(
        frame_generator(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@require_http_methods(["GET"])
def congestion_status(request, file_name):
    """특정 스트림의 현재 혼잡도 상태를 JSON으로 반환합니다."""
    # start_processor_if_not_running 제거 - 영상 종료 후 폴링으로 프로세서가 재시작되는 문제 방지
    status = cache.get(f'{file_name}_current_congestion_status', {
            "level": 1, "label": "측정중", "occupancy": 0, "object_count": 0
        })
    return JsonResponse(status)

@require_http_methods(["GET"])
def congestion_graph_view(request, file_name):
    """특정 스트림의 혼잡도 이력 그래프 이미지를 반환합니다."""
    # start_processor_if_not_running 제거 - 영상 종료 후 폴링으로 프로세서가 재시작되는 문제 방지
    history = cache.get(f'{file_name}_congestion_history')

    if not history:
        return HttpResponse("아직 데이터가 수집되지 않았습니다.", status=204)

    timestamps, counts = zip(*history)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(timestamps, counts, color='skyblue', label='Occupation')
    ax1.plot(timestamps, counts, color='red', marker='o', linestyle='-', label='Trend')
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Occupation / Trend")
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend()
    fig.suptitle('Time-based Congestion Rate')
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    
    return HttpResponse(buf.getvalue(), content_type='image/png')

@require_http_methods(["GET"])
def confirm_processor_alive(request):
    """활성화된 비디오 프로세서가 있는지 확인합니다."""
    if stream_manager.get_active_processors():
        return JsonResponse({'status': "실시간 모니터링 중"})
    else:
        return JsonResponse({'status': "대기 중"})

# --- 2. 전역 예측 시스템(Predictor) API 뷰 ---

@require_http_methods(["GET"])
@predictor_api_view # ✨ 데코레이터 적용
def get_predictions(request, predictor: RealtimeCongestionPredictor):
    """예측 결과 반환"""    
    predictions = predictor.predict()
    
    return JsonResponse({
        'predictions': predictions,
        'timestamp': datetime.now().isoformat()
    })

