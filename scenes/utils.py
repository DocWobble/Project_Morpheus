"""Helpers for running scenario scenes and capturing artifacts.

`scenes` modules use these utilities to drive the orchestrator with a mock
``TTSAdapter`` while collecting a timeline and WAV file for auditing.  The
primary entry point is :func:`run_scene`, which executes a scene and writes the
resulting artifacts to disk.
"""

import asyncio
import json
import time
import wave
from pathlib import Path

from orchestrator.buffer import PlaybackBuffer
from orchestrator.chunk_ladder import ChunkLadder
from orchestrator.core import Orchestrator


def run_scene(scene_name: str, adapter, tmp_path: Path, barge_in_at: int | None = None):
    """Run a scene and capture timeline + WAV artifacts.

    Parameters
    ----------
    scene_name: str
        Name used for artifact files.
    adapter: TTSAdapter
        Adapter providing :class:`AudioChunk` instances.
    tmp_path: Path
        Directory to write artifacts into.
    barge_in_at: int | None
        If provided, signal a barge-in after this many chunks.
    """
    buffer = PlaybackBuffer(capacity_ms=1000)
    orch = Orchestrator(adapter, buffer, ChunkLadder())
    timeline: list[dict] = []
    audio_bytes = bytearray()
    start = time.perf_counter()

    async def _run():
        chunk_id = 0
        async for chunk in orch.stream():
            now = (time.perf_counter() - start) * 1000.0
            audio_bytes.extend(chunk.pcm)
            timeline.append(
                {
                    "chunk_id": chunk_id,
                    "adapter": getattr(adapter, "name", adapter.__class__.__name__),
                    "timestamp_ms": now,
                    "duration_ms": chunk.duration_ms,
                    "buffer_ms": buffer.depth_ms,
                }
            )
            if barge_in_at is not None and chunk_id == barge_in_at:
                orch.signal_barge_in()
            chunk_id += 1

    asyncio.run(_run())

    wav_path = tmp_path / f"{scene_name}.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_bytes)

    timeline_path = tmp_path / f"{scene_name}.json"
    with open(timeline_path, "w", encoding="utf-8") as fh:
        json.dump(timeline, fh, indent=2)

    return timeline_path, wav_path, timeline
