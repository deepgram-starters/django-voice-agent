"""WebSocket URL routing"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('api/voice-agent', consumers.VoiceAgentConsumer.as_asgi()),
]
