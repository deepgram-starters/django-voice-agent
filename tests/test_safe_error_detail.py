import os
import unittest
import asyncio
import json

os.environ.setdefault("DEEPGRAM_API_KEY", "test-api-key")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from deepgram.core.api_error import ApiError
from deepgram.agent.v1.client import AsyncV1SocketClient
from starter.consumers import _safe_error_detail
from starter.consumers import VoiceAgentConsumer


class SafeErrorDetailTests(unittest.TestCase):
    def test_api_error_does_not_expose_authorization_header(self):
        detail = _safe_error_detail(
            ApiError(
                status_code=401,
                headers={"Authorization": "Token FAKE"},
                body="invalid credentials",
            )
        )

        self.assertIn("HTTP 401", detail)
        self.assertNotIn("FAKE", detail)

    def test_generic_error_is_not_described_as_a_connection_failure(self):
        self.assertEqual(
            "Deepgram operation failed (RuntimeError)",
            _safe_error_detail(RuntimeError()),
        )

    def test_all_supported_control_messages_reach_typed_senders(self):
        class Connection:
            def __init__(self):
                self.calls = []

            async def send_function_call_response(self, message):
                self.calls.append(("FunctionCallResponse", message))

            async def send_keep_alive(self, message):
                self.calls.append(("KeepAlive", message))

            async def send_update_listen(self, message):
                self.calls.append(("UpdateListen", message))

            async def send_update_think(self, message):
                self.calls.append(("UpdateThink", message))

            async def send_inject_agent_message(self, message):
                self.calls.append(("InjectAgentMessage", message))

        async def exercise():
            consumer = object.__new__(VoiceAgentConsumer)
            consumer.connection = Connection()
            for message_type in (
                "FunctionCallResponse",
                "KeepAlive",
                "UpdateListen",
                "UpdateThink",
                "InjectAgentMessage",
            ):
                await consumer.receive(text_data=json.dumps({"type": message_type}))
            return consumer.connection.calls

        calls = asyncio.run(exercise())
        self.assertEqual([message_type for message_type, _ in calls], [
            "FunctionCallResponse",
            "KeepAlive",
            "UpdateListen",
            "UpdateThink",
            "InjectAgentMessage",
        ])

    def test_update_listen_serializes_provider_to_deepgram(self):
        class WebSocket:
            def __init__(self):
                self.sent = []

            async def send(self, message):
                self.sent.append(message)

        async def exercise(model):
            websocket = WebSocket()
            consumer = object.__new__(VoiceAgentConsumer)
            consumer.connection = AsyncV1SocketClient(websocket=websocket)
            await consumer.receive(text_data=json.dumps({
                "type": "UpdateListen",
                "listen": {"provider": {"type": "deepgram", "model": model}},
            }))
            return websocket.sent

        for model, version in (("nova-3", "v1"), ("flux-general-en", "v2")):
            with self.subTest(model=model):
                sent = asyncio.run(exercise(model))
                self.assertEqual([{
                    "type": "UpdateListen",
                    "listen": {"provider": {
                        "version": version,
                        "type": "deepgram",
                        "model": model,
                    }},
                }], [json.loads(message) for message in sent])
