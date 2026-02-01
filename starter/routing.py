"""WebSocket URL routing"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('agent/converse', consumers.VoiceAgentConsumer.as_asgi()),
]
