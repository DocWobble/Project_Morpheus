import asyncio
import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub out optional dependencies that require system libraries
sys.modules.setdefault("sounddevice", types.SimpleNamespace())

from morpheus_tts.tts_engine.orpheus_local import SAMPLE_RATE, TTSAdapter


class DummyAdapter(TTSAdapter):
    """TTSAdapter with a predictable PCM generator for testing."""

    async def _ensure_gen(self) -> None:  # type: ignore[override]
        if self._gen is None and not self._exhausted:
            async def gen():
                yield b"\x00" * 100

            self._gen = gen()


def test_pull_respects_chunk_size():
    adapter = DummyAdapter(prompt="hi")
    chunk_ms = 0.5
    chunk_bytes = int(chunk_ms / 1000 * SAMPLE_RATE * 2)

    async def run():
        chunks = []
        while True:
            chunk = await adapter.pull(chunk_bytes)
            chunks.append(chunk)
            if chunk.eos:
                break
        return chunks

    chunks = asyncio.run(run())

    assert all(len(c.pcm) == chunk_bytes for c in chunks[:-1])
    assert len(chunks[-1].pcm) == 100 - chunk_bytes * (len(chunks) - 1)
    assert chunks[-1].eos
    assert all(len(c.pcm) <= chunk_bytes for c in chunks)

