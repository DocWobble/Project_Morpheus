"""Barge-In scenario."""
from orchestrator.adapter import AudioChunk, TTSAdapter

from .utils import run_scene


class BargeAdapter(TTSAdapter):
    """Emit chunks until barge-in occurs."""

    def __init__(self, total: int = 5) -> None:
        self.total = total
        self.sent = 0
        self.reset_called = False

    async def pull(self, _size):
        if self.sent >= self.total:
            return AudioChunk(pcm=b"", duration_ms=0, eos=True)
        self.sent += 1
        return AudioChunk(pcm=b"\x05\x00" * 160, duration_ms=10, eos=False)

    async def reset(self):  # pragma: no cover - trivial
        self.reset_called = True


def run(tmp_path):
    """Run Barge-In and record artifacts."""
    adapter = BargeAdapter()
    timeline_path, wav_path, timeline = run_scene("barge_in", adapter, tmp_path, barge_in_at=2)
    return (
        timeline_path,
        wav_path,
        {
            "timeline": timeline,
            "reset_called": adapter.reset_called,
            "planned_chunks": adapter.total,
        },
    )
