"""HTTP URL routing"""
from django.urls import path
from . import views

urlpatterns = [
    path('session', views.get_session, name='session'),
    path('metadata', views.metadata, name='metadata'),
]
