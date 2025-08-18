"""Mid-Stream Swap scenario."""
from Morpheus_Client.orchestrator.adapter import AudioChunk, TTSAdapter

from .utils import run_scene


class SwapAdapter(TTSAdapter):
    """Swap adapter identity mid-stream."""

    def __init__(self, switch_after: int = 3, total: int = 6) -> None:
        self.name = "adapter_a"
        self.switch_after = switch_after
        self.total = total
        self.sent = 0

    async def pull(self, _size):
        if self.sent >= self.total:
            return AudioChunk(pcm=b"", duration_ms=0, eos=True)
        self.sent += 1
        pcm = (b"\x03\x00" if self.name == "adapter_a" else b"\x04\x00") * 160
        if self.sent == self.switch_after:
            self.name = "adapter_b"
        eos = self.sent >= self.total
        return AudioChunk(pcm=pcm, duration_ms=10, eos=eos)

    async def reset(self):  # pragma: no cover - trivial
        return None


def run(tmp_path):
    """Run Mid-Stream Swap and record artifacts."""
    adapter = SwapAdapter()
    timeline_path, wav_path, timeline = run_scene("mid_stream_swap", adapter, tmp_path)
    return timeline_path, wav_path, {"timeline": timeline}
