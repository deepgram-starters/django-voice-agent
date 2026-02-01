"""HTTP URL routing"""
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
import os

def index(request):
    index_path = os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse("Build frontend first", status=404)

urlpatterns = [
    path('', index),
    path('api/', include('starter.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
