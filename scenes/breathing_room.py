"""Breathing Room scenario."""
from morpheus_tts.orchestrator.adapter import AudioChunk, TTSAdapter

from .utils import run_scene


class BreathingAdapter(TTSAdapter):
    """Emit a couple of short chunks then EOS."""

    def __init__(self) -> None:
        self.chunks = [
            AudioChunk(pcm=b"\x01\x00" * 160, duration_ms=10, eos=False),
            AudioChunk(pcm=b"\x01\x00" * 160, duration_ms=10, eos=True),
        ]

    async def pull(self, _size):
        if self.chunks:
            return self.chunks.pop(0)
        return AudioChunk(pcm=b"", duration_ms=0, eos=True)

    async def reset(self):  # pragma: no cover - trivial
        return None


def run(tmp_path):
    """Run Breathing Room and record artifacts."""
    adapter = BreathingAdapter()
    timeline_path, wav_path, timeline = run_scene("breathing_room", adapter, tmp_path)
    return timeline_path, wav_path, {"timeline": timeline}
