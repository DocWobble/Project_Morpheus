import asyncio
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Morpheus_Client.orchestrator.adapter import AudioChunk
from Morpheus_Client.orchestrator.stitcher import stitch_chunks


async def collect_chunks(it):
    return [c async for c in it]


def pcm_from_ints(vals):
    return struct.pack('<' + 'h'*len(vals), *vals)


def test_stitch_overlap_add():
    sample_rate = 1000  # 1 sample == 1ms
    # two 6-sample chunks with 2-sample overlap
    a = AudioChunk(pcm=pcm_from_ints([0,1,2,3,4,5]), duration_ms=6)
    b = AudioChunk(pcm=pcm_from_ints([5,4,3,2,1,0]), duration_ms=6, eos=True)

    async def gen():
        yield a
        yield b

    stitched = asyncio.run(collect_chunks(stitch_chunks(gen(), sample_rate=sample_rate, overlap_ms=2)))
    pcm = np.frombuffer(b''.join(c.pcm for c in stitched), dtype=np.int16)
    assert list(pcm) == [0,1,2,3,4,4,3,2,1,0]


def test_stitch_optional_markers():
    sample_rate = 1000
    a = AudioChunk(pcm=pcm_from_ints([0,1]), duration_ms=2, markers="A")
    b = AudioChunk(pcm=pcm_from_ints([1,0]), duration_ms=2, markers="B", eos=True)

    async def gen():
        yield a
        yield b

    # markers suppressed by default
    out = asyncio.run(collect_chunks(stitch_chunks(gen(), sample_rate=sample_rate)))
    assert all(c.markers is None for c in out)

    # markers propagated when enabled
    out = asyncio.run(collect_chunks(stitch_chunks(gen(), sample_rate=sample_rate, emit_markers=True)))
    assert [c.markers for c in out] == ["A", "B"]
