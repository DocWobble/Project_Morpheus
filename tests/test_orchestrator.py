import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from morpheus_tts.orchestrator.adapter import AudioChunk, TTSAdapter
from morpheus_tts.orchestrator.buffer import PlaybackBuffer
from morpheus_tts.orchestrator.chunk_ladder import ChunkLadder
from morpheus_tts.orchestrator.core import Orchestrator
from morpheus_tts.orchestrator.ring_buffer import RingBuffer


class DummyAdapter(TTSAdapter):
    """Simple adapter that returns pre-seeded chunks."""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.reset_called = False

    async def pull(self, _size):
        if self.chunks:
            return self.chunks.pop(0)
        return AudioChunk(pcm=b"", duration_ms=0, eos=True)

    async def reset(self):
        self.reset_called = True


def test_stream_stops_on_eos():
    chunk = AudioChunk(pcm=b"", duration_ms=10, eos=True)
    adapter = DummyAdapter([chunk])
    orch = Orchestrator(adapter, PlaybackBuffer(capacity_ms=500), ChunkLadder())

    async def run():
        return [c async for c in orch.stream()]

    output = asyncio.run(run())
    assert len(output) == 1
    assert output[0].eos


def test_barge_in_resets_adapter():
    chunk = AudioChunk(pcm=b"", duration_ms=10, eos=False)
    adapter = DummyAdapter([chunk])
    buffer = PlaybackBuffer(capacity_ms=500)
    orch = Orchestrator(adapter, buffer, ChunkLadder())

    async def run():
        async for _ in orch.stream():
            orch.signal_barge_in()

    asyncio.run(run())
    assert adapter.reset_called
    assert buffer.depth_ms == 0


def test_ring_buffer_tracks_playback():
    buffer = PlaybackBuffer(capacity_ms=1000)
    ring = RingBuffer(capacity=320, sample_rate=16000, playback=buffer)
    written = ring.write(b"\x00" * 320)  # 10ms at 16 kHz
    assert written == 320
    assert buffer.depth_ms == pytest.approx(10.0)
    ring.read(160)  # consume 5ms
    assert buffer.depth_ms == pytest.approx(5.0)
