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
from pathlib import Path
from typing import AsyncGenerator, Callable, Tuple

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
        self.timeline: list[dict] = []
        self.transcripts: list[dict] = []

    def _record(self, stage: str, start: float, result: str) -> None:
        """Append a timing event to the in-memory timeline."""
        duration_ms = (time.perf_counter() - start) * 1000.0
        self.timeline.append({"stage": stage, "duration_ms": duration_ms, "result": result})

    def signal_barge_in(self) -> None:
        """Notify the orchestrator that the current utterance was interrupted."""
        self._barge_in.set()

    def log_transcript(self, text: str) -> None:
        """Record a transcript entry for later inspection."""
        self.transcripts.append({"timestamp": time.time(), "text": text})

    def save_timeline(self, path: str | Path) -> None:
        """Persist current timeline, metrics and transcripts to ``path``."""
        payload = {
            "events": self.timeline,
            "metrics": {"events": len(self.timeline)},
        }
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        transcript_path = out.parent / "transcripts.json"
        with open(transcript_path, "w", encoding="utf-8") as fh:
            json.dump(self.transcripts, fh, indent=2)

    async def stream(
        self, on_event: Callable[[dict], None] | None = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """Yield audio chunks until EOS or a barge-in occurs.

        Parameters
        ----------
        on_event: Callable[[dict], None] | None, optional
            If provided, this callable is invoked with a JSON-serialisable
            dictionary describing each emitted chunk.  The payload matches the
            structured log entry and includes ``chunk_id``, ``adapter``,
            ``token_window`` and ``render_ms`` along with the base64-encoded
            PCM data.
        """
        chunk_id = 0
        while not self._barge_in.is_set():
            adapter_name = getattr(self.adapter, "name", self.adapter.__class__.__name__)
            window = self.ladder.current
            start = time.perf_counter()
            chunk = await self.adapter.pull(window)
            render_ms = (time.perf_counter() - start) * 1000.0
            self._record("adapter_pull", start, "eos" if chunk.eos else "ok")

            log_entry = {
                "chunk_id": chunk_id,
                "adapter": adapter_name,
                "token_window": window,
                "render_ms": render_ms,
                "pcm": base64.b64encode(chunk.pcm).decode("ascii"),
            }
            logger.info(json.dumps(log_entry))
            if on_event is not None:
                on_event(log_entry)

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
            start = time.perf_counter()
            await self.adapter.reset()
            self.buffer.reset()
            if self.ring is not None:
                self.ring.reset()
            self._barge_in.clear()
            self._record("barge_in_reset", start, "ok")
