"""Cold Start scenario."""
import asyncio
from Morpheus_Client.orchestrator.adapter import AudioChunk, TTSAdapter

from .utils import run_scene


class ColdStartAdapter(TTSAdapter):
    """Simulate warm-up delay on first chunk."""

    def __init__(self, total: int = 3) -> None:
        self.total = total
        self.sent = 0

    async def pull(self, _size):
        if self.sent == 0:
            # emulate expensive warm-up on first request
            await asyncio.sleep(0.05)
        if self.sent >= self.total:
            return AudioChunk(pcm=b"", duration_ms=0, eos=True)
        self.sent += 1
        return AudioChunk(pcm=b"\x01\x00" * 160, duration_ms=10, eos=False)

    async def reset(self):  # pragma: no cover - trivial
        return None


def run(tmp_path):
    """Run Cold Start and record artifacts."""
    adapter = ColdStartAdapter()
    timeline_path, wav_path, timeline = run_scene("cold_start", adapter, tmp_path)
    return timeline_path, wav_path, {"timeline": timeline}
