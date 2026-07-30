"""
WebSocket consumer for Voice Agent

Bridges the browser to Deepgram's Voice Agent API (agent.v1) via the SDK.
Browser control messages (JSON) are dispatched to the matching typed SDK send
method; microphone audio (binary) is streamed with send_media. Agent responses
(JSON models and binary audio) are forwarded back to the browser unchanged.
"""
import os
import json
import asyncio

import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from dotenv import load_dotenv

from deepgram import AsyncDeepgramClient
from deepgram.environment import DeepgramClientEnvironment
from deepgram.core.unchecked_base_model import construct_type
from deepgram.agent.v1.types import (
    AgentV1Settings,
    AgentV1UpdateSpeak,
    AgentV1UpdatePrompt,
    AgentV1InjectUserMessage,
)
from starter.views import SESSION_SECRET

load_dotenv()

API_KEY = os.environ.get("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable is required")


# One async SDK client, reused across connections; the browser never sees the API key.
# DEEPGRAM_BASE_URL overrides the default agent endpoint (e.g. a staging host).
def _build_client():
    base_url = os.environ.get("DEEPGRAM_BASE_URL")
    if base_url:
        https = base_url.replace("wss://", "https://").replace("ws://", "http://")
        env = DeepgramClientEnvironment(
            base=https, production=base_url, agent=base_url, agent_rest=https
        )
        print(f"Using custom Deepgram base URL: {base_url}")
        return AsyncDeepgramClient(api_key=API_KEY, environment=env)
    return AsyncDeepgramClient(api_key=API_KEY)


deepgram = _build_client()


class VoiceAgentConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None
        self._connection_cm = None
        self.forward_task = None

    async def connect(self):
        """Accept WebSocket connection and open the Deepgram agent connection."""
        # Validate JWT from subprotocol
        protocols = self.scope.get("subprotocols", [])
        valid_proto = None
        for proto in protocols:
            if proto.startswith("access_token."):
                token = proto[len("access_token."):]
                try:
                    jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
                    valid_proto = proto
                except Exception:
                    pass
                break

        if not valid_proto:
            await self.close(code=4401)
            return

        await self.accept(subprotocol=valid_proto)
        print("Client connected to /api/voice-agent")

        try:
            # `connect()` is an async context manager; enter it manually so the
            # connection lives across the consumer's connect/disconnect lifecycle.
            self._connection_cm = deepgram.agent.v1.connect()
            self.connection = await self._connection_cm.__aenter__()
            print("Connected to Deepgram Agent API")

            self.forward_task = asyncio.create_task(self.forward_from_deepgram())

        except Exception as error:
            print(f"Error connecting to Deepgram: {error}")
            await self.send(text_data=json.dumps({
                "type": "Error",
                "description": str(error),
                "code": "CONNECTION_FAILED"
            }))
            await self.close()

    async def disconnect(self, close_code):
        """Clean up Deepgram connection"""
        print(f"Client disconnected with code: {close_code}")

        if self.forward_task and not self.forward_task.done():
            self.forward_task.cancel()
            try:
                await self.forward_task
            except asyncio.CancelledError:
                pass

        if self._connection_cm:
            try:
                await self._connection_cm.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing Deepgram connection: {e}")

    async def receive(self, text_data=None, bytes_data=None):
        """Forward client messages to Deepgram: audio via send_media, JSON via typed sends."""
        if not self.connection:
            return
        try:
            if bytes_data:
                await self.connection.send_media(bytes_data)
                return
            if not text_data:
                return

            try:
                data = json.loads(text_data)
            except (ValueError, TypeError):
                print("Ignoring non-JSON message from client")
                return

            msg_type = data.get("type")
            if msg_type == "Settings":
                await self.connection.send_settings(construct_type(type_=AgentV1Settings, object_=data))
            elif msg_type == "UpdateSpeak":
                await self.connection.send_update_speak(construct_type(type_=AgentV1UpdateSpeak, object_=data))
            elif msg_type == "UpdatePrompt":
                await self.connection.send_update_prompt(construct_type(type_=AgentV1UpdatePrompt, object_=data))
            elif msg_type == "InjectUserMessage":
                await self.connection.send_inject_user_message(
                    construct_type(type_=AgentV1InjectUserMessage, object_=data)
                )
            else:
                print(f"Ignoring unknown client message type: {msg_type}")
        except Exception as error:
            print(f"Error forwarding to Deepgram: {error}")
            await self.send(text_data=json.dumps({
                "type": "Error",
                "description": str(error),
                "code": "PROVIDER_ERROR"
            }))

    async def forward_from_deepgram(self):
        """Forward Deepgram messages to the browser: bytes as binary, models as JSON."""
        try:
            async for message in self.connection:
                if isinstance(message, (bytes, bytearray)):
                    await self.send(bytes_data=bytes(message))
                elif hasattr(message, "model_dump_json"):
                    await self.send(text_data=message.model_dump_json())
                else:
                    await self.send(text_data=json.dumps(
                        {"type": getattr(message, "type", "Unknown")}
                    ))
        except asyncio.CancelledError:
            pass
        except Exception as error:
            print(f"Error forwarding from Deepgram: {error}")
        finally:
            # Close client connection when Deepgram closes (preserves original code).
            try:
                await self.close(code=3000)
            except Exception:
                pass
