"""Adapter protocol for PCM generation.

Defines the pull-based interface adapters must implement so that the
orchestrator can request audio chunks as needed.  This keeps the hot
path streaming-only and lets the orchestrator control chunk sizes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class AudioChunk:
    """A unit of PCM audio returned by an adapter.

    Attributes
    ----------
    pcm:
        Raw PCM16 little-endian audio data.  The orchestrator treats this
        as opaque bytes and writes it into the playback ring buffer.
    duration_ms:
        Duration of ``pcm`` in milliseconds.
    markers:
        Optional backend specific metadata (e.g. word boundaries).
    eos:
        End-of-stream marker.  When ``True`` the adapter has no further
        audio for the current request.
    """

    pcm: bytes
    duration_ms: float
    markers: Optional[object] = None
    eos: bool = False


class TTSAdapter(Protocol):
    """Protocol that all synthesis backends must satisfy.

    The orchestrator drives synthesis by repeatedly calling ``pull`` with
    a target chunk size.  Implementations must return as soon as a chunk
    is ready; they may return smaller chunks than requested but must not
    block waiting for an entire utterance.
    """

    async def pull(self, chunk_size: int) -> AudioChunk:
        """Return the next chunk of audio.

        Parameters
        ----------
        chunk_size:
            Desired chunk granularity in adapter native units (tokens or
            milliseconds).  Adapters may return less but should never
            exceed this amount.
        """
        ...

    async def reset(self) -> None:
        """Reset any internal state after a barge-in event."""
        ...
