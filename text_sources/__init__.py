"""Pluggable text source interfaces.

Defines the :class:`TextSource` protocol used to obtain chunks of
text from different origins such as WebSocket feeds, HTTP polling or
local CLI pipes.  Adapters implementing this protocol are registered
with :mod:`text_sources.registry`.
"""
from __future__ import annotations

from typing import AsyncGenerator, Protocol


class TextSource(Protocol):
    """Protocol that all text source adapters must satisfy.

    Implementations yield chunks of text on demand.  The orchestrator
    or host service consumes the async generator to receive new text.
    """

    async def stream(self) -> AsyncGenerator[str, None]:
        """Yield text chunks until the source is exhausted."""
        ...
