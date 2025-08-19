"""Text source adapter reading from a CLI pipe."""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Dict, Any

from . import TextSource


class CLIPipeSource(TextSource):
    """Yield lines from an ``asyncio`` ``StreamReader``."""

    def __init__(self, reader: asyncio.StreamReader) -> None:
        self.reader = reader

    async def stream(self) -> AsyncGenerator[str, None]:
        while True:
            line = await self.reader.readline()
            if not line:
                break
            yield line.decode().rstrip("\n")


def describe() -> Dict[str, Any]:
    return {
        "name": "cli_pipe",
        "streaming": True,
        "unit": "msgs",
        "granularity": ["line"],
        "stateful_context": "none",
    }
