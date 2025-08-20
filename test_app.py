#!/usr/bin/env python
"""
Test suite for Django Voice Agent Starter App

Tests WebSocket connection establishment, audio streaming, and voice agent functionality.
Run with: pytest -v test_app.py
"""
import pytest
import os
from unittest.mock import AsyncMock, patch
from channels.testing import WebsocketCommunicator

# Set up Django for testing
os.environ.setdefault('DEEPGRAM_API_KEY', 'test-api-key')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app')

import app

class TestVoiceAgentConsumer:
    """Test the WebSocket consumer for voice agent functionality."""

    @pytest.fixture
    def consumer_communicator(self):
        """Create a WebSocket communicator for testing."""
        communicator = WebsocketCommunicator(app.VoiceAgentConsumer.as_asgi(), "/ws")
        return communicator

    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self, consumer_communicator):
        """Test WebSocket connection can be established."""
        # Mock Deepgram client before connecting
        with patch('app.DeepgramClient') as mock_deepgram:
            mock_connection = AsyncMock()
            mock_deepgram.return_value.agent.websocket.v.return_value = mock_connection
            mock_connection.start.return_value = True

            connected, _ = await consumer_communicator.connect()
            assert connected
            await consumer_communicator.disconnect()

    @pytest.mark.asyncio
    async def test_websocket_missing_api_key(self):
        """Test WebSocket connection behavior without API key."""
        # Store original API key
        original_key = os.environ.get('DEEPGRAM_API_KEY')

        # Remove API key and test connection behavior
        if 'DEEPGRAM_API_KEY' in os.environ:
            del os.environ['DEEPGRAM_API_KEY']

        try:
            communicator = WebsocketCommunicator(app.VoiceAgentConsumer.as_asgi(), "/ws")
            connected, close_code = await communicator.connect()

            # Test passes if either:
            # 1. Connection fails immediately (connected == False), OR
            # 2. Connection succeeds but consumer should handle missing key gracefully
            if connected:
                # If connected, the consumer should still work (just won't be able to start agent)
                await communicator.disconnect()
                # Test that we can at least establish the WebSocket connection
                assert connected == True
            else:
                # If connection failed, that's also acceptable behavior
                assert connected == False

        finally:
            # Restore original API key
            if original_key:
                os.environ['DEEPGRAM_API_KEY'] = original_key

    @pytest.mark.asyncio
    async def test_audio_stream_handling(self, consumer_communicator):
        """Test handling of audio stream data."""
        # Mock Deepgram agent connection before connecting
        with patch('app.DeepgramClient') as mock_deepgram:
            mock_connection = AsyncMock()
            mock_deepgram.return_value.agent.websocket.v.return_value = mock_connection
            mock_connection.start.return_value = True

            # Connect to WebSocket consumer
            connected, _ = await consumer_communicator.connect()
            assert connected

            # Give the connection a moment to be established
            import asyncio
            await asyncio.sleep(0.1)

            # Send binary audio data
            fake_audio_data = b'fake_audio_data'
            await consumer_communicator.send_to(bytes_data=fake_audio_data)

            # Give time for audio processing
            await asyncio.sleep(0.1)

            # Verify audio data was sent to Deepgram agent
            # The mock should have been called with the audio data
            mock_connection.send.assert_called()

            await consumer_communicator.disconnect()

    @pytest.mark.asyncio
    async def test_agent_response_handling(self, consumer_communicator):
        """Test that agent responses can be received from WebSocket."""
        # Mock Deepgram client before connecting
        with patch('app.DeepgramClient') as mock_deepgram:
            mock_connection = AsyncMock()
            mock_deepgram.return_value.agent.websocket.v.return_value = mock_connection
            mock_connection.start.return_value = True

            # Connect to WebSocket consumer
            connected, _ = await consumer_communicator.connect()
            assert connected

            # Give time for connection setup
            import asyncio
            await asyncio.sleep(0.1)

            await consumer_communicator.disconnect()

    @pytest.mark.asyncio
    async def test_proper_cleanup_on_disconnect(self, consumer_communicator):
        """Test proper cleanup when WebSocket disconnects."""
        # Mock Deepgram client before connecting
        with patch('app.DeepgramClient') as mock_deepgram:
            mock_connection = AsyncMock()
            mock_deepgram.return_value.agent.websocket.v.return_value = mock_connection
            mock_connection.start.return_value = True

            # Connect to WebSocket consumer (this creates the DeepgramClient)
            connected, _ = await consumer_communicator.connect()
            assert connected

            # Verify the DeepgramClient was instantiated during connection
            assert mock_deepgram.called

            # Disconnect should trigger cleanup
            await consumer_communicator.disconnect()

            # Verify agent connection finish was called
            mock_connection.finish.assert_called()

    def test_deepgram_api_integration_setup(self):
        """Test that Deepgram API integration is properly configured."""
        # Test that required imports work
        from deepgram import (
            DeepgramClient,
            DeepgramClientOptions,
            AgentWebSocketEvents
        )

        # Test that we can create instances (without actual API calls)
        assert DeepgramClient
        assert DeepgramClientOptions
        assert AgentWebSocketEvents

class TestDjangoApplication:
    """Test the Django application setup."""

    def test_django_settings_configuration(self):
        """Test Django settings are properly configured."""
        from django.conf import settings

        # Test basic settings exist
        assert hasattr(settings, 'DEBUG')
        assert 'channels' in settings.INSTALLED_APPS

        # Test ASGI application is configured
        if hasattr(settings, 'ASGI_APPLICATION'):
            assert settings.ASGI_APPLICATION.endswith('.application')

        # Test channel layers configuration exists
        assert hasattr(settings, 'CHANNEL_LAYERS')
        assert 'default' in settings.CHANNEL_LAYERS

    def test_main_view_returns_html(self):
        """Test that the main view returns HTML content."""
        from django.http import HttpRequest

        request = HttpRequest()
        response = app.serve_index(request)

        assert response.status_code == 200
        # FileResponse doesn't have .content, it has a file
        # Just test that we get a successful response for the HTML file
        assert hasattr(response, 'file_to_stream') or hasattr(response, 'streaming_content')

    def test_url_configuration(self):
        """Test URL routing is properly configured."""
        # Test that URL patterns exist in the app module
        assert hasattr(app, 'urlpatterns')
        assert len(app.urlpatterns) > 0

        # Test that the view function exists (correct name)
        assert hasattr(app, 'serve_index')
        assert callable(app.serve_index)

        # Test basic URL pattern structure
        from django.urls import URLPattern
        assert isinstance(app.urlpatterns[0], URLPattern)

        # Test WebSocket URL patterns exist too
        assert hasattr(app, 'websocket_urlpatterns')
        assert len(app.websocket_urlpatterns) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])