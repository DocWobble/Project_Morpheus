"""Orpheus TTS adapter for local PCM streaming.

This adapter wraps :func:`generate_speech_from_api` and translates its
output into :class:`~morpheus_tts.orchestrator.adapter.AudioChunk`
objects.  The underlying generator may yield PCM segments of arbitrary
size, so we maintain an internal buffer and slice the data to honour the
``chunk_size`` requested by the orchestrator.  ``chunk_size`` is the
maximum number of PCM bytes that a returned
:class:`~morpheus_tts.orchestrator.adapter.AudioChunk` may contain.
This keeps the adapter agnostic to the sample rate while guaranteeing
bounded chunk sizes.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from ..orchestrator.adapter import (
    AudioChunk,
    TTSAdapter as TTSAdapterProtocol,
)

from .inference import (
    generate_speech_from_api,
    SAMPLE_RATE,
    DEFAULT_VOICE,
)


class TTSAdapter(TTSAdapterProtocol):
    """Concrete adapter that streams PCM audio from the Orpheus API."""

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
        self._buffer = bytearray()
        self._exhausted = False

    async def _ensure_gen(self) -> None:
        if self._gen is None and not self._exhausted:
            self._gen = await generate_speech_from_api(
                prompt=self.prompt,
                voice=self.voice,
                use_batching=self.use_batching,
                max_batch_chars=self.max_batch_chars,
            )

    async def pull(self, chunk_size: int) -> AudioChunk:
        """Return the next chunk of PCM audio.

        Parameters
        ----------
        chunk_size:
            Maximum number of PCM bytes to return.  The adapter slices
            the buffered stream so that ``AudioChunk.pcm`` never exceeds
            this value.
        """

        target_bytes = chunk_size

        await self._ensure_gen()

        while len(self._buffer) < target_bytes and not self._exhausted:
            assert self._gen is not None
            try:
                self._buffer.extend(await self._gen.__anext__())
            except StopAsyncIteration:
                self._exhausted = True
                break

        if not self._buffer and self._exhausted:
            return AudioChunk(pcm=b"", duration_ms=0.0, eos=True)

        pcm = bytes(self._buffer[:target_bytes])
        del self._buffer[:target_bytes]
        duration_ms = len(pcm) / 2 / SAMPLE_RATE * 1000.0
        eos = self._exhausted and len(self._buffer) == 0
        return AudioChunk(pcm=pcm, duration_ms=duration_ms, eos=eos)

    async def reset(self) -> None:
        """Reset internal generator after a barge-in event."""

        self._gen = None
        self._buffer.clear()
        self._exhausted = False


__all__ = ["TTSAdapter"]

