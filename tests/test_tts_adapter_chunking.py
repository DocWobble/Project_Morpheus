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
    chunk_ms = 1
    target_bytes = int(chunk_ms / 1000 * SAMPLE_RATE * 2)

    async def run():
        return [await adapter.pull(chunk_ms) for _ in range(3)]

    first, second, third = asyncio.run(run())

    assert len(first.pcm) == target_bytes
    assert len(second.pcm) == target_bytes
    assert len(third.pcm) == 100 - 2 * target_bytes
    assert third.eos
    assert all(len(c.pcm) <= target_bytes for c in (first, second))

