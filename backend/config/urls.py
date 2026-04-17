from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.conf.urls.static import static

def main_page(request):
    """메인 페이지를 렌더링하는 뷰 함수"""
    return render(request, 'project.html', {})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stream/', include('backend.videostream.urls')),
    path('', main_page, name='main'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)