"""Minimal client for interacting with a running Morpheus TTS server."""
from __future__ import annotations

from typing import AsyncGenerator
from urllib.parse import quote

import httpx
import websockets
from websockets.exceptions import ConnectionClosedOK

from .tts_engine import DEFAULT_VOICE


class Client:
    """Helper for streaming audio from the Morpheus TTS server."""

    def __init__(self, base_url: str = "http://localhost:5005") -> None:
        self.base_url = base_url.rstrip("/")

    async def stream_rest(self, text: str, voice: str = DEFAULT_VOICE) -> AsyncGenerator[bytes, None]:
        """Stream WAV bytes from the REST endpoint."""
        url = f"{self.base_url}/v1/audio/speech"
        headers = {"Accept": "audio/wav"}
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", url, json={"input": text, "voice": voice}, headers=headers
            ) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk

    async def stream_ws(self, text: str, voice: str = DEFAULT_VOICE) -> AsyncGenerator[bytes, None]:
        """Stream WAV bytes from the WebSocket endpoint."""
        ws_url = self.base_url.replace("http", "ws") + f"/ws/tts?prompt={quote(text)}&voice={quote(voice)}"
        async with websockets.connect(ws_url) as ws:
            while True:
                try:
                    data = await ws.recv()
                except ConnectionClosedOK:
                    break
                yield data

