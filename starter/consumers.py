"""WebSocket consumer for Voice Agent"""
import os
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions as STTOptions,
    SpeakWebSocketEvents,
    SpeakWSOptions,
)
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable is required")

deepgram = DeepgramClient(api_key=API_KEY)


class VoiceAgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accept WebSocket connection and setup Deepgram connections"""
        await self.accept()
        print("Client connected to /agent/stream")

        # Store connection references
        self.stt_connection = None
        self.tts_connection = None

    async def disconnect(self, close_code):
        """Clean up Deepgram connections"""
        print(f"Client disconnected with code: {close_code}")
        if self.stt_connection:
            await self.stt_connection.finish()
        if self.tts_connection:
            await self.tts_connection.close()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive messages from WebSocket.
        First message: JSON config with model/language settings
        Subsequent messages: Audio bytes from user
        """
        try:
            # First message is configuration
            if text_data:
                config = json.loads(text_data)
                stt_model = config.get('stt_model', 'nova-2')
                tts_model = config.get('tts_model', 'aura-asteria-en')
                language = config.get('language', 'en')

                # Create STT connection
                self.stt_connection = deepgram.listen.asyncwebsocket.v("1")

                async def on_stt_message(self, result, **kwargs):
                    """Handle transcription results"""
                    sentence = result.channel.alternatives[0].transcript
                    if len(sentence) > 0 and result.is_final:
                        print(f"User said: {sentence}")

                        # Process with agent logic (placeholder)
                        response_text = f"I heard: {sentence}"

                        # Send to TTS
                        if self.tts_connection:
                            await self.tts_connection.send_text(response_text)

                async def on_stt_error(self, error, **kwargs):
                    """Handle STT errors"""
                    print(f"STT error: {error}")
                    await self.send(text_data=json.dumps({
                        'error': f'STT: {error}'
                    }))

                self.stt_connection.on(LiveTranscriptionEvents.Transcript, on_stt_message)
                self.stt_connection.on(LiveTranscriptionEvents.Error, on_stt_error)

                # Start STT connection
                stt_options = STTOptions(
                    model=stt_model,
                    language=language,
                    smart_format=True,
                    interim_results=False,
                )

                if await self.stt_connection.start(stt_options):
                    print(f"STT connection started with model={stt_model}")
                else:
                    print("Failed to start STT connection")
                    await self.close()
                    return

                # Create TTS connection
                self.tts_connection = deepgram.speak.asyncwebsocket.v("1")

                async def on_tts_binary(self, data, **kwargs):
                    """Forward audio to client"""
                    await self.send(bytes_data=data)

                async def on_tts_error(self, error, **kwargs):
                    """Handle TTS errors"""
                    print(f"TTS error: {error}")

                self.tts_connection.on(SpeakWebSocketEvents.AudioData, on_tts_binary)
                self.tts_connection.on(SpeakWebSocketEvents.Error, on_tts_error)

                # Start TTS connection
                tts_options = SpeakWSOptions(
                    model=tts_model,
                    encoding="linear16",
                    sample_rate=16000,
                )

                if await self.tts_connection.start(tts_options):
                    print(f"TTS connection started with model={tts_model}")
                else:
                    print("Failed to start TTS connection")
                    await self.close()

            # Subsequent messages are audio data from user
            elif bytes_data and self.stt_connection:
                await self.stt_connection.send(bytes_data)

        except Exception as e:
            print(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
