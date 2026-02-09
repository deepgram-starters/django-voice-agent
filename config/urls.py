from django.urls import path, include
from starter.views import serve_index

urlpatterns = [
    path('', serve_index, name='index'),
    path('api/', include('starter.urls')),
]
