import os
import logging

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    AgentWebSocketEvents,
    SettingsOptions,
    FunctionCallRequest,
    FunctionCallResponse,
    Input,
    Output,
)

# ============================================================================
# DJANGO CONFIGURATION & SETUP
# ============================================================================

# Configure Django settings inline - all settings in one place for single-file app
if not settings.configured:
    settings.configure(
        DEBUG=os.getenv('DEBUG', 'True').lower() in ('true', '1', 't'),
        SECRET_KEY=os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production'),
        ALLOWED_HOSTS=['localhost', '127.0.0.1', '[::1]'],
        INSTALLED_APPS=[
            'channels',  # Required for WebSocket support
        ],
        ROOT_URLCONF=__name__,  # URL configuration is defined in this module
        ASGI_APPLICATION=f'{__name__}.application',  # ASGI app for WebSocket support
        CHANNEL_LAYERS={
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer',
            },
        },
        LOGGING={
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                },
            },
            'root': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    )
    django.setup()

# ============================================================================
# DJANGO IMPORTS & CONFIGURATION
# ============================================================================

import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.core.asgi import get_asgi_application
from django.http import FileResponse, Http404
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.generic.websocket import AsyncWebsocketConsumer


# DEEPGRAM_API_KEY is sourced directly from the environment
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to track if the binary data warning has been printed
# This is to adhere to the example from app-requirements.
warning_notice_printed = False

# ============================================================================
# DJANGO HTTP VIEWS
# ============================================================================

def serve_index(request):
    """
    Serves the index.html file for the voice agent web interface.

    This view handles the root URL and returns the HTML page that contains
    the JavaScript client for connecting to the WebSocket and handling audio.
    """
    try:
        return FileResponse(open('./index.html', 'rb'))
    except FileNotFoundError:
        raise Http404("index.html not found")

# ============================================================================
# DJANGO CHANNELS WEBSOCKET CONSUMER
# ============================================================================

class VoiceAgentConsumer(AsyncWebsocketConsumer):
    """
    Django Channels WebSocket consumer for handling voice agent connections.

    This consumer manages the WebSocket connection between the browser client
    and the Deepgram Voice Agent API. It handles:
    - WebSocket connection establishment
    - Deepgram Voice Agent configuration and connection
    - Audio streaming from browser to Deepgram
    - Event handling from Deepgram (conversation text, agent responses, etc.)
    - Connection cleanup
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dg_connection = None

    async def connect(self):
        """Handle WebSocket connection."""
        global warning_notice_printed
        warning_notice_printed = False  # Reset for each new connection

        await self.accept()
        logger.info("Browser WebSocket connection established.")

        try:
            # Configure Deepgram client
            config: DeepgramClientOptions = DeepgramClientOptions(
                options={
                    "keepalive": "true",
                    "microphone_record": "true",
                    "speaker_playback": "true",
                }
            )
            deepgram: DeepgramClient = DeepgramClient(DEEPGRAM_API_KEY, config)
            self.dg_connection = deepgram.agent.websocket.v("1")
            logger.info("Deepgram client configured and WebSocket connection object created.")

            # Configure and start Deepgram connection
            options: SettingsOptions = SettingsOptions()

            # Configure audio input settings
            options.audio.input = Input(
                encoding="linear16",
                sample_rate=16000  # Match the output sample rate
            )

            # Configure audio output settings
            options.audio.output = Output(
                encoding="linear16",
                sample_rate=16000,
                container="none"
            )

            # LLM provider configuration
            options.agent.think.provider.type = "open_ai"
            options.agent.think.provider.model = "gpt-4o-mini"
            options.agent.think.prompt = (
                "You are a helpful voice assistant created by Deepgram. "
                "Your responses should be friendly, human-like, and conversational. "
                "Always keep your answers concise—1-2 sentences, no more than 120 characters.\n\n"
                "When responding to a user\'s message, follow these guidelines:\n"
                "- If the user\'s message is empty, respond with an empty message.\n"
                "- Ask follow-up questions to engage the user, but only one question at a time.\n"
                "- Keep your responses unique and avoid repetition.\n"
                "- If a question is unclear or ambiguous, ask for clarification before answering.\n"
                "- If asked about your well-being, provide a brief response about how you\'re feeling.\n\n"
                "Remember that you have a voice interface. You can listen and speak, and all your "
                "responses will be spoken aloud."
            )

            # Deepgram provider configuration
            options.agent.listen.provider.keyterms = ["hello", "goodbye"]
            options.agent.listen.provider.model = "nova-3"
            options.agent.listen.provider.type = "deepgram"
            options.agent.speak.provider.type = "deepgram"

            # Sets Agent greeting
            options.agent.greeting = "Hello! I\'m your Deepgram voice assistant. How can I help you today?"

            # ----------------------------------------------------------------
            # DEEPGRAM EVENT HANDLERS
            # ----------------------------------------------------------------
            # Define event handlers for Deepgram Voice Agent events
            # These handlers process various events from the Deepgram API
            def on_open(self, open_event, **kwargs):
                logger.info(f"Deepgram Connection Open: {open_event}")

            def on_binary_data(self, data, **kwargs):
                global warning_notice_printed
                if not warning_notice_printed:
                    logger.info("Received binary data from Deepgram.")
                    logger.info("If speaker_playback is true, SDK should handle playback.")
                    logger.info("Otherwise, you can process this binary data (e.g., send to browser).")
                    warning_notice_printed = True
                # If speaker_playback isn't working or you need to manually send to browser:
                # You could send data to browser using self.send(bytes_data=data)

            def on_welcome(self, welcome, **kwargs):
                logger.info(f"Deepgram Welcome: {welcome}")

            def on_settings_applied(self, settings_applied, **kwargs):
                logger.info(f"Deepgram Settings Applied: {settings_applied}")

            def on_conversation_text(self, conversation_text, **kwargs):
                logger.info(f"Deepgram Conversation Text: {conversation_text}")

            def on_user_started_speaking(self, user_started_speaking, **kwargs):
                logger.info(f"Deepgram User Started Speaking: {user_started_speaking}")

            def on_agent_thinking(self, agent_thinking, **kwargs):
                logger.info(f"Deepgram Agent Thinking: {agent_thinking}")

            def on_function_call_request(self, function_call_request: FunctionCallRequest, **kwargs):
                logger.info(f"Deepgram Function Call Request: {function_call_request}")
                try:
                    # Example: Respond to a function call.
                    # You might want to implement more sophisticated logic here.
                    response = FunctionCallResponse(
                        function_call_id=function_call_request.function_call_id,
                        output=f"Function call '{function_call_request.name}' processed successfully with args: {function_call_request.arguments}",
                    )
                    self.dg_connection.send_function_call_response(response)
                    logger.info(f"Sent function call response for ID: {function_call_request.function_call_id}")
                except Exception as e:
                    logger.error(f"Error in function call handling: {e}")

            def on_agent_started_speaking(self, agent_started_speaking, **kwargs):
                logger.info(f"Deepgram Agent Started Speaking: {agent_started_speaking}")

            def on_agent_audio_done(self, agent_audio_done, **kwargs):
                logger.info(f"Deepgram Agent Audio Done: {agent_audio_done}")

            def on_close(self, close_event, **kwargs):
                logger.info(f"Deepgram Connection Close: {close_event}")

            def on_error(self, error, **kwargs):
                logger.error(f"Deepgram Error: {error}")

            def on_unhandled(self, unhandled, **kwargs):
                logger.warning(f"Deepgram Unhandled Event: {unhandled}")

            # Register event handlers
            self.dg_connection.on(AgentWebSocketEvents.Open, on_open)
            self.dg_connection.on(AgentWebSocketEvents.AudioData, on_binary_data)
            self.dg_connection.on(AgentWebSocketEvents.Welcome, on_welcome)
            self.dg_connection.on(AgentWebSocketEvents.SettingsApplied, on_settings_applied)
            self.dg_connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
            self.dg_connection.on(AgentWebSocketEvents.UserStartedSpeaking, on_user_started_speaking)
            self.dg_connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
            self.dg_connection.on(AgentWebSocketEvents.FunctionCallRequest, on_function_call_request)
            self.dg_connection.on(AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking)
            self.dg_connection.on(AgentWebSocketEvents.AgentAudioDone, on_agent_audio_done)
            self.dg_connection.on(AgentWebSocketEvents.Close, on_close)
            self.dg_connection.on(AgentWebSocketEvents.Error, on_error)
            self.dg_connection.on(AgentWebSocketEvents.Unhandled, on_unhandled)

            logger.info("Starting Deepgram connection...")
            if not self.dg_connection.start(options):
                logger.error("Failed to start Deepgram connection.")
                await self.close(code=1011)
                return

        except Exception as e:
            logger.error(f"Error in WebSocket connection setup: {e}", exc_info=True)
            await self.close(code=1011)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info("Browser WebSocket connection closing.")
        if self.dg_connection:
            logger.info("Finishing Deepgram connection.")
            self.dg_connection.finish()
        logger.info("Browser WebSocket connection closed.")

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if bytes_data:
                # Send binary audio data to Deepgram
                if self.dg_connection:
                    self.dg_connection.send(bytes_data)
            elif text_data:
                logger.info(f"Received text from browser WebSocket: {text_data}")
                # Potentially handle text commands from browser if needed in future
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}", exc_info=True)

# ============================================================================
# DJANGO URL CONFIGURATION AND ASGI APPLICATION
# ============================================================================

# Django HTTP URL patterns
urlpatterns = [
    path('', serve_index, name='index'),  # Serve index.html at root URL
]

# WebSocket URL patterns for Django Channels
websocket_urlpatterns = [
    path('ws', VoiceAgentConsumer.as_asgi()),  # WebSocket endpoint for voice agent
]

# ASGI application with both HTTP and WebSocket routing
# This combines regular HTTP requests with WebSocket connections
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handle regular HTTP requests
    "websocket": URLRouter(websocket_urlpatterns),  # Handle WebSocket connections
})

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

def main():
    """
    Main function to run the Django voice agent server.

    This function:
    - Validates required environment variables (DEEPGRAM_API_KEY)
    - Starts the Daphne ASGI server on localhost:8080
    - Handles graceful shutdown on Ctrl+C
    """
    if not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY environment variable not set. Please set it and try again.")
        return

    import daphne.server

    logger.info("Starting Django voice agent server on http://localhost:8080")
    logger.info("Open index.html in your browser to interact.")
    logger.info("Press Ctrl+C to stop the server.")

    # Run the server using Daphne (ASGI server for Django Channels)
    try:
        daphne.server.run(
            application,
            endpoints=['tcp:port=8080:interface=127.0.0.1'],
            verbosity=1
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()