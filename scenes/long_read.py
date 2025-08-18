"""Long Read scenario."""
from Morpheus_Client.orchestrator.adapter import AudioChunk, TTSAdapter

from .utils import run_scene


class LongReadAdapter(TTSAdapter):
    """Emit many uniform chunks to simulate a long narration."""

    def __init__(self, total: int = 60) -> None:
        self.total = total
        self.sent = 0

    async def pull(self, _size):
        if self.sent >= self.total:
            return AudioChunk(pcm=b"", duration_ms=0, eos=True)
        self.sent += 1
        eos = self.sent >= self.total
        return AudioChunk(pcm=b"\x02\x00" * 160, duration_ms=10, eos=eos)

    async def reset(self):  # pragma: no cover - trivial
        return None


def run(tmp_path):
    """Run Long Read and record artifacts."""
    adapter = LongReadAdapter()
    timeline_path, wav_path, timeline = run_scene("long_read", adapter, tmp_path)
    return timeline_path, wav_path, {"timeline": timeline}
