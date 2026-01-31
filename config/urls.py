"""HTTP URL routing"""
from django.urls import path, include
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path('api/', include('starter.urls')),
]

# Serve static files (frontend)
if settings.DEBUG:
    urlpatterns.append(
        path('', serve, {'path': 'index.html', 'document_root': settings.STATIC_ROOT}),
    )
