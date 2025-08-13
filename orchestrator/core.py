"""High-level PCM orchestrator.

This module coordinates PCM generation by pulling from a TTS adapter,
monitoring playback buffer levels and adapting chunk size accordingly.  It
also exposes hooks for barge-in signalling so an external component can
interrupt synthesis at a frame boundary.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Tuple

from .adapter import AudioChunk, TTSAdapter
from .buffer import PlaybackBuffer
from .chunk_ladder import ChunkLadder


class Orchestrator:
    """Coordinate PCM generation and adaptive pacing."""

    def __init__(
        self,
        adapter: TTSAdapter,
        buffer: PlaybackBuffer,
        ladder: ChunkLadder | None = None,
        comfort_band: Tuple[float, float] = (50.0, 250.0),
    ) -> None:
        self.adapter = adapter
        self.buffer = buffer
        self.ladder = ladder or ChunkLadder()
        self.comfort_band = comfort_band
        self._barge_in = asyncio.Event()

    def signal_barge_in(self) -> None:
        """Notify the orchestrator that the current utterance was interrupted."""
        self._barge_in.set()

    async def stream(self) -> AsyncGenerator[AudioChunk, None]:
        """Yield audio chunks until EOS or a barge-in occurs."""
        while not self._barge_in.is_set():
            chunk = await self.adapter.pull(self.ladder.current)
            self.buffer.add(chunk.duration_ms)
            yield chunk
            if chunk.eos:
                break
            self._adapt_chunk_size()
        if self._barge_in.is_set():
            await self.adapter.reset()
            self.buffer.reset()
            self._barge_in.clear()

    def _adapt_chunk_size(self) -> None:
        """Adjust chunk size based on buffer depth."""
        low, high = self.comfort_band
        if self.buffer.depth_ms < low:
            self.ladder.step_up()
        elif self.buffer.depth_ms > high:
            self.ladder.step_down()
