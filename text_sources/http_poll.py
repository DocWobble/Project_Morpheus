"""Text source adapter that polls an HTTP endpoint."""
from __future__ import annotations

from typing import AsyncGenerator, Dict, Any

import httpx

from . import TextSource


class HTTPPollingSource(TextSource):
    """Retrieve text by repeatedly GETting an HTTP endpoint."""

    def __init__(self, url: str, client: httpx.AsyncClient | None = None) -> None:
        self.url = url
        self._client = client or httpx.AsyncClient()

    async def stream(self) -> AsyncGenerator[str, None]:
        async with self._client as client:
            while True:
                resp = await client.get(self.url)
                text = resp.text.strip()
                if not text:
                    break
                yield text


def describe() -> Dict[str, Any]:
    return {
        "name": "http_poll",
        "streaming": False,
        "unit": "msgs",
        "granularity": ["line"],
        "stateful_context": "none",
    }
