import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

# Mock DEEPGRAM_API_KEY before importing app or its components that might use it
os.environ["DEEPGRAM_API_KEY"] = "test_api_key"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["DEBUG"] = "True"

class TestVoiceAgentServer(TestCase):
    """Test cases for the Django Voice Agent server."""

    def setUp(self):
        """Set up test environment."""
        # Ensure environment variables are set for testing
        if not os.getenv("DEEPGRAM_API_KEY"):
            os.environ["DEEPGRAM_API_KEY"] = "mock_deepgram_api_key_for_testing"

    @database_sync_to_async
    def test_index_view(self):
        """Test that the index view serves the HTML file."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    async def test_websocket_connection(self):
        """
        Tests if a WebSocket client can successfully connect to the /ws endpoint.
        """
        # Mock the DeepgramClient and its methods to prevent actual API calls during tests
        with patch('app.DeepgramClient') as MockDeepgramClient:
            # Configure the mock for dg_connection.start() to return True
            mock_dg_instance = MockDeepgramClient.return_value
            mock_dg_connection = MagicMock()
            mock_dg_connection.start.return_value = True  # Simulate successful start
            mock_dg_instance.agent.websocket.v.return_value = mock_dg_connection

            # Import the consumer after mocking
            from app import VoiceAgentConsumer

            communicator = WebsocketCommunicator(VoiceAgentConsumer.as_asgi(), "/ws")
            connected, subprotocol = await communicator.connect()

            self.assertTrue(connected, "WebSocket connection should be established")

            # Clean up
            await communicator.disconnect()

    async def test_deepgram_agent_creation_and_start(self):
        """
        Tests that the Deepgram agent connection is attempted and started successfully (mocked).
        """
        with patch('app.DeepgramClient') as MockDeepgramClient:
            mock_dg_instance = MockDeepgramClient.return_value
            mock_dg_connection = MagicMock()
            mock_dg_connection.start.return_value = True  # Simulate successful start
            mock_dg_instance.agent.websocket.v.return_value = mock_dg_connection

            # Import the consumer after mocking
            from app import VoiceAgentConsumer

            communicator = WebsocketCommunicator(VoiceAgentConsumer.as_asgi(), "/ws")
            connected, subprotocol = await communicator.connect()

            self.assertTrue(connected, "WebSocket should remain open if Deepgram agent starts.")
            mock_dg_connection.start.assert_called_once()

            # Close the connection
            await communicator.disconnect()

            # Ensure finish is called on the Deepgram connection when the ws closes
            mock_dg_connection.finish.assert_called_once()

    @unittest_run_loop
    async def test_handle_audio_data_from_client(self):
        """
        Tests if the server correctly receives binary audio data from the client
        and attempts to send it to the (mocked) Deepgram connection.
        """
        with patch('app.DeepgramClient') as MockDeepgramClient:
            mock_dg_instance = MockDeepgramClient.return_value
            mock_dg_connection = MagicMock()
            mock_dg_connection.start.return_value = True
            mock_dg_instance.agent.websocket.v.return_value = mock_dg_connection

            async with self.client.ws_connect('/ws') as ws:
                self.assertFalse(ws.closed, "WebSocket connection should be open.")

                # Send mock audio data
                mock_audio_data = b'\x01\x02\x03\x04\x05'
                await ws.send_bytes(mock_audio_data)

                # Give a brief moment for the server to process the message
                await asyncio.sleep(0.01)

                # Check if the mocked Deepgram connection's send method was called with the audio data
                mock_dg_connection.send.assert_called_once_with(mock_audio_data)

# To run these tests, you would typically use:
# pytest test_app.py