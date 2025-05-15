import pytest
import asyncio
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch, MagicMock

# Mock DEEPGRAM_API_KEY before importing app or its components that might use it
import os
os.environ["DEEPGRAM_API_KEY"] = "test_api_key"

# It's common to refactor aiohttp app setup into a function for testability
# If your app.py doesn't have `create_app()`, we'll need to adjust it or this test structure.
# For now, let's assume `app.py` will be modified to have:
# async def create_app():
#     app = web.Application()
#     # ... (add routes, etc.)
#     return app

class TestVoiceAgentServer(AioHTTPTestCase):
    async def get_application(self):
        """
        Override to return the aiohttp.web.Application instance.
        """
        # We need to ensure DEEPGRAM_API_KEY is set before app logic runs
        if not os.getenv("DEEPGRAM_API_KEY"):
            os.environ["DEEPGRAM_API_KEY"] = "mock_deepgram_api_key_for_testing"

        # Dynamically import app components after setting env var
        # and potentially after patching DeepgramClient if needed for deeper tests.
        from app import serve_index, websocket_handler

        app = web.Application()
        app.router.add_get('/', serve_index)
        app.router.add_get('/ws', websocket_handler)
        return app

    @unittest_run_loop
    async def test_websocket_connection(self):
        """
        Tests if a WebSocket client can successfully connect to the /ws endpoint.
        """
        # Mock the DeepgramClient and its methods to prevent actual API calls during tests
        with patch('app.DeepgramClient') as MockDeepgramClient:
            # Configure the mock for dg_connection.start() to return True
            mock_dg_instance = MockDeepgramClient.return_value
            mock_dg_connection = MagicMock()
            mock_dg_connection.start.return_value = True # Simulate successful start
            mock_dg_instance.agent.websocket.v.return_value = mock_dg_connection

            async with self.client.ws_connect('/ws') as ws:
                self.assertEqual(ws.closed, False, "WebSocket connection should be open.")

                # Optional: Check for an initial message from server if your app sends one upon connection
                # For example, if Deepgram agent sends a welcome message that gets logged or proxied.
                # This current app.py doesn't directly proxy DG's welcome to browser client.

                # Close the WebSocket connection from the client side for cleanup
                await ws.close()
            self.assertEqual(ws.closed, True, "WebSocket connection should be closed after test.")

    @unittest_run_loop
    async def test_deepgram_agent_creation_and_start(self):
        """
        Tests that the Deepgram agent connection is attempted and started successfully (mocked).
        """
        with patch('app.DeepgramClient') as MockDeepgramClient:
            mock_dg_instance = MockDeepgramClient.return_value
            mock_dg_connection = MagicMock()
            mock_dg_connection.start.return_value = True  # Simulate successful start
            mock_dg_instance.agent.websocket.v.return_value = mock_dg_connection

            async with self.client.ws_connect('/ws') as ws:
                # The connection itself and mock_dg_connection.start being called (implicitly by ws_connect)
                # is the primary check here. If start wasn't called or returned False and was handled,
                # the ws might close or an error might be logged (which could be asserted too).
                self.assertFalse(ws.closed, "WebSocket should remain open if Deepgram agent starts.")
                mock_dg_connection.start.assert_called_once()

            # Ensure finish is called on the Deepgram connection when the ws closes
            # This depends on how your app.py's finally block is structured.
            # Assuming dg_connection.finish() is called.
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