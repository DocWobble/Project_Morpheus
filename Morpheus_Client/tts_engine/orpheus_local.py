"""Orpheus TTS adapter for local PCM streaming.

Audio is generated using a locally loaded :class:`OrpheusCpp` model.  The
model is cached at module scope so subsequent calls reuse the same
instance.  The underlying generator may yield PCM segments of arbitrary
size, so we maintain an internal buffer and slice the data to honour the
``chunk_size`` requested by the orchestrator.  ``chunk_size`` is the
maximum number of PCM bytes that a returned
:class:`~Morpheus_Client.orchestrator.adapter.AudioChunk` may contain.
This keeps the adapter agnostic to the sample rate while guaranteeing
bounded chunk sizes.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import AsyncGenerator, Optional, TYPE_CHECKING

from ..orchestrator.adapter import (
    AudioChunk,
    TTSAdapter as TTSAdapterProtocol,
)

from .inference import (
    SAMPLE_RATE,
    DEFAULT_VOICE,
)

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from orpheus_cpp import OrpheusCpp


_model_lock = asyncio.Lock()


@lru_cache(maxsize=1)
def _load_model_sync() -> "OrpheusCpp":
    """Load and cache the underlying :class:`OrpheusCpp` model."""

    from orpheus_cpp import OrpheusCpp

    # ``verbose`` is disabled to keep logs clean during tests; language is fixed
    # to English which matches the default voice set.
    return OrpheusCpp(verbose=False, lang="en")


async def _load_model() -> "OrpheusCpp":
    """Thread-safe coroutine returning the cached :class:`OrpheusCpp` instance."""

    async with _model_lock:
        return _load_model_sync()


async def _stream_from_model(
    model: "OrpheusCpp",
    prompt: str,
    voice: str,
    *_: object,
) -> AsyncGenerator[bytes, None]:
    """Asynchronously stream PCM chunks from ``model``.

    The underlying ``OrpheusCpp.stream_tts_sync`` method is synchronous.  We
    execute each ``next`` call in a thread via :func:`asyncio.to_thread` to avoid
    blocking the event loop.
    """

    gen = model.stream_tts_sync(prompt, options={"voice_id": voice})
    while True:
        result = await asyncio.to_thread(lambda: next(gen, None))
        if result is None:
            break
        _sr, chunk = result
        yield chunk.tobytes()


class TTSAdapter(TTSAdapterProtocol):
    """Concrete adapter that streams PCM audio from a local Orpheus model."""

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
            model = await _load_model()
            self._gen = _stream_from_model(
                model,
                self.prompt,
                self.voice,
                self.use_batching,
                self.max_batch_chars,
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

