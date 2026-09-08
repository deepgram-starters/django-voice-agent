import os
import unittest
import asyncio
import json
from unittest.mock import patch

os.environ.setdefault("DEEPGRAM_API_KEY", "test-api-key")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from deepgram.core.api_error import ApiError
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
            with patch("starter.consumers.construct_type", side_effect=lambda **kwargs: kwargs["object_"]):
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
