from django.urls import path
from . import views

urlpatterns = [
    path('<str:file_name>/', views.live_stream_view, name='live_stream_view'),
    path('status/<str:file_name>/', views.congestion_status, name='congestion_status'),
    path('graph/<str:file_name>/', views.congestion_graph_view, name='congestion_graph'),
    path('video/check-processor/', views.confirm_processor_alive, name='check_processor'),
    path('api/predictions/', views.get_predictions, name='predictions'),
]