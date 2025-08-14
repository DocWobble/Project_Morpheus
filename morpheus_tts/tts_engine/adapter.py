from __future__ import annotations

from typing import AsyncGenerator, Optional

from ..orchestrator.adapter import AudioChunk, TTSAdapter as TTSAdapterProtocol

from .inference import (
    generate_speech_from_api,
    SAMPLE_RATE,
    DEFAULT_VOICE,
)


class TTSAdapter(TTSAdapterProtocol):
    """Concrete adapter that wraps ``generate_speech_from_api``.

    The adapter exposes the protocol expected by the orchestrator by
    lazily initialising the underlying PCM generator on first use and
    translating its output into :class:`AudioChunk` objects.
    """

    def __init__(
        self,
        prompt: str,
        voice: str = DEFAULT_VOICE,
        *,
        use_batching: bool = False,
        max_batch_chars: int = 1000,
    ) -> None:
        self.prompt = prompt
        self.voice = voice
        self.use_batching = use_batching
        self.max_batch_chars = max_batch_chars
        self._gen: Optional[AsyncGenerator[bytes, None]] = None

    async def _ensure_gen(self) -> None:
        if self._gen is None:
            self._gen = await generate_speech_from_api(
                prompt=self.prompt,
                voice=self.voice,
                use_batching=self.use_batching,
                max_batch_chars=self.max_batch_chars,
            )

    async def pull(self, chunk_size: int) -> AudioChunk:  # chunk_size ignored for now
        await self._ensure_gen()
        assert self._gen is not None
        try:
            pcm = await self._gen.__anext__()
        except StopAsyncIteration:
            return AudioChunk(pcm=b"", duration_ms=0.0, eos=True)

        duration_ms = len(pcm) / 2 / SAMPLE_RATE * 1000.0
        return AudioChunk(pcm=pcm, duration_ms=duration_ms)

    async def reset(self) -> None:
        """Reset internal generator after a barge-in event."""
        self._gen = None
