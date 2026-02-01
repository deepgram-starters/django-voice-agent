"""
WebSocket consumer for Voice Agent

Simple pass-through proxy to Deepgram's Voice Agent API.
Forwards all messages (JSON and binary) bidirectionally between client and Deepgram.
"""
import os
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import websockets
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("DEEPGRAM_API_KEY")
if not API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable is required")


class VoiceAgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accept WebSocket connection and create Deepgram proxy"""
        await self.accept()
        print("Client connected to /agent/converse")

        try:
            # Connect to Deepgram Agent API
            deepgram_url = "wss://agent.deepgram.com/v1/agent/converse"

            self.deepgram_ws = await websockets.connect(
                deepgram_url,
                additional_headers={
                    "Authorization": f"Token {API_KEY}"
                }
            )
            print("✓ Connected to Deepgram Agent API")

            # Start forwarding task
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

        # Cancel forwarding task
        if hasattr(self, 'forward_task') and not self.forward_task.done():
            self.forward_task.cancel()
            try:
                await self.forward_task
            except asyncio.CancelledError:
                pass

        # Close Deepgram connection
        if hasattr(self, 'deepgram_ws'):
            try:
                await self.deepgram_ws.close()
            except Exception as e:
                print(f"Error closing Deepgram connection: {e}")

    async def receive(self, text_data=None, bytes_data=None):
        """Forward all messages from client to Deepgram"""
        try:
            if hasattr(self, 'deepgram_ws'):
                if text_data:
                    await self.deepgram_ws.send(text_data)
                elif bytes_data:
                    await self.deepgram_ws.send(bytes_data)
        except Exception as error:
            print(f"Error forwarding to Deepgram: {error}")
            await self.send(text_data=json.dumps({
                "type": "Error",
                "description": str(error),
                "code": "PROVIDER_ERROR"
            }))

    async def forward_from_deepgram(self):
        """Forward all messages from Deepgram to client"""
        try:
            async for message in self.deepgram_ws:
                if isinstance(message, bytes):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except websockets.exceptions.ConnectionClosed:
            print("Deepgram connection closed")
        except Exception as error:
            print(f"Error forwarding from Deepgram: {error}")
        finally:
            # Close client connection when Deepgram closes
            await self.close(code=3000)
