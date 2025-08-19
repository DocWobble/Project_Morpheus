"""Text source adapter reading from a WebSocket feed."""
from __future__ import annotations

from typing import AsyncGenerator, Dict, Any

import websockets

from . import TextSource


class WebSocketSource(TextSource):
    """Receive text messages from a WebSocket server."""

    def __init__(self, uri: str) -> None:
        self.uri = uri

    async def stream(self) -> AsyncGenerator[str, None]:
        async with websockets.connect(self.uri) as ws:
            async for message in ws:
                yield message


def describe() -> Dict[str, Any]:
    return {
        "name": "websocket",
        "streaming": True,
        "unit": "msgs",
        "granularity": ["line"],
        "stateful_context": "rolling",
    }
