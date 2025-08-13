"""High-level PCM orchestrator.

This module coordinates PCM generation by pulling from a TTS adapter,
monitoring playback buffer levels and adapting chunk size accordingly.  It
also exposes hooks for barge-in signalling so an external component can
interrupt synthesis at a frame boundary.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import AsyncGenerator, Tuple

from .adapter import AudioChunk, TTSAdapter
from .buffer import PlaybackBuffer
from .chunk_ladder import ChunkLadder
from .ring_buffer import RingBuffer


logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinate PCM generation and adaptive pacing."""

    def __init__(
        self,
        adapter: TTSAdapter,
        buffer: PlaybackBuffer,
        ladder: ChunkLadder | None = None,
        comfort_band: Tuple[float, float] = (50.0, 250.0),
        ring: RingBuffer | None = None,
    ) -> None:
        self.adapter = adapter
        self.buffer = buffer
        self.ladder = ladder or ChunkLadder()
        self.comfort_band = comfort_band
        self.ring = ring
        self._barge_in = asyncio.Event()

    def signal_barge_in(self) -> None:
        """Notify the orchestrator that the current utterance was interrupted."""
        self._barge_in.set()

    async def stream(self) -> AsyncGenerator[AudioChunk, None]:
        """Yield audio chunks until EOS or a barge-in occurs."""
        chunk_id = 0
        adapter_name = getattr(self.adapter, "name", self.adapter.__class__.__name__)
        while not self._barge_in.is_set():
            window = self.ladder.current
            start = time.perf_counter()
            chunk = await self.adapter.pull(window)
            render_ms = (time.perf_counter() - start) * 1000.0

            log_entry = {
                "chunk_id": chunk_id,
                "adapter": adapter_name,
                "token_window": window,
                "render_ms": render_ms,
                "pcm": base64.b64encode(chunk.pcm).decode("ascii"),
            }
            logger.info(json.dumps(log_entry))

            if self.ring is not None:
                self.ring.write(chunk.pcm)
            else:
                self.buffer.add(chunk.duration_ms)

            yield chunk
            if chunk.eos:
                break
            self.ladder.adapt(self.buffer.depth_ms, self.comfort_band)
            chunk_id += 1
        if self._barge_in.is_set():
            await self.adapter.reset()
            self.buffer.reset()
            if self.ring is not None:
                self.ring.reset()
            self._barge_in.clear()
