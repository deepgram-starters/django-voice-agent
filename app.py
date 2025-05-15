import asyncio
import os
import logging
from aiohttp import web, WSMsgType

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

# DEEPGRAM_API_KEY is now sourced directly from the environment
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to track if the binary data warning has been printed
# This is to adhere to the example from app-requirements.
warning_notice_printed = False

async def serve_index(request):
    """Serves the index.html file."""
    # We will create index.html in a subsequent step
    return web.FileResponse('./index.html')

async def websocket_handler(request):
    """Handles WebSocket connections for audio streaming and Deepgram interaction."""
    global warning_notice_printed
    warning_notice_printed = False  # Reset for each new connection

    ws_browser = web.WebSocketResponse()
    await ws_browser.prepare(request)

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
        dg_connection = deepgram.agent.websocket.v("1")
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

        # Define Deepgram event handlers
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
            # loop = asyncio.get_event_loop()
            # asyncio.run_coroutine_threadsafe(ws_browser.send_bytes(data), loop)


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
                dg_connection.send_function_call_response(response)
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
        dg_connection.on(AgentWebSocketEvents.Open, on_open)
        dg_connection.on(AgentWebSocketEvents.AudioData, on_binary_data) # Renamed from on_binary_data to match SDK
        dg_connection.on(AgentWebSocketEvents.Welcome, on_welcome)
        dg_connection.on(AgentWebSocketEvents.SettingsApplied, on_settings_applied)
        dg_connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
        dg_connection.on(AgentWebSocketEvents.UserStartedSpeaking, on_user_started_speaking)
        dg_connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
        dg_connection.on(AgentWebSocketEvents.FunctionCallRequest, on_function_call_request)
        dg_connection.on(AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking)
        dg_connection.on(AgentWebSocketEvents.AgentAudioDone, on_agent_audio_done)
        dg_connection.on(AgentWebSocketEvents.Close, on_close)
        dg_connection.on(AgentWebSocketEvents.Error, on_error)
        dg_connection.on(AgentWebSocketEvents.Unhandled, on_unhandled)

        logger.info("Starting Deepgram connection...")
        if not dg_connection.start(options):
            logger.error("Failed to start Deepgram connection.")
            await ws_browser.close(code=1011, message="Failed to connect to Deepgram agent")
            return

        # Main loop to receive audio from browser and send to Deepgram
        async for msg in ws_browser:
            if msg.type == WSMsgType.BINARY:
                dg_connection.send(msg.data)
            elif msg.type == WSMsgType.TEXT:
                logger.info(f"Received text from browser WebSocket: {msg.data}")
                # Potentially handle text commands from browser if needed in future
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"Browser WebSocket connection closed with exception {ws_browser.exception()}")
                break # Exit loop on error

    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
        await ws_browser.close(code=1011, message=f"Server error: {e}")
    finally:
        logger.info("Browser WebSocket connection closing.")
        if 'dg_connection' in locals() and dg_connection:
            logger.info("Finishing Deepgram connection.")
            dg_connection.finish()
        await ws_browser.close() # Ensure browser WebSocket is closed
        logger.info("Browser WebSocket connection closed.")

    return ws_browser

def main():
    if not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY environment variable not set. Please set it and try again.")
        return

    app = web.Application()
    app.router.add_get('/', serve_index)
    app.router.add_get('/ws', websocket_handler)

    logger.info("Starting web server on http://localhost:8080")
    logger.info("Open index.html in your browser to interact.")
    logger.info("Press Ctrl+C to stop the server.")
    web.run_app(app, port=8080)

if __name__ == "__main__":
    main()