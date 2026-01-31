"""HTTP URL routing"""
from django.urls import path
from . import views

urlpatterns = [
    path('metadata', views.metadata, name='metadata'),
]
