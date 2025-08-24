"""Llama.cpp TTS adapter for local PCM streaming.

Audio is generated using a locally loaded :class:`llama_cpp.Llama` model.  The
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
import os

from ..orchestrator.adapter import (
    AudioChunk,
    TTSAdapter as TTSAdapterProtocol,
)

from .inference import (
    SAMPLE_RATE,
    DEFAULT_VOICE,
)

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from llama_cpp import Llama


_model_lock = asyncio.Lock()


@lru_cache(maxsize=1)
def _load_model_sync() -> "Llama":
    """Load and cache the underlying :class:`llama_cpp.Llama` model."""

    from llama_cpp import Llama

    model_path = os.environ.get("LLAMA_MODEL_PATH", "model.gguf")
    n_ctx = int(os.environ.get("LLAMA_N_CTX", "8192"))
    n_gpu_layers = int(os.environ.get("LLAMA_N_GPU_LAYERS", "0"))

    return Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
    )


async def _load_model() -> "Llama":
    """Thread-safe coroutine returning the cached :class:`llama_cpp.Llama` instance."""

    async with _model_lock:
        return _load_model_sync()


async def _stream_from_model(
    model: "Llama",
    prompt: str,
    voice: str,
    *_: object,
) -> AsyncGenerator[bytes, None]:
    """Asynchronously stream PCM chunks from ``model``.

    The underlying ``Llama.text_to_speech`` method is synchronous.  We
    execute each ``next`` call in a thread via :func:`asyncio.to_thread` to avoid
    blocking the event loop.  The iterator is expected to yield either raw
    PCM ``bytes`` or ``(sample_rate, chunk)`` tuples where ``chunk`` exposes
    a ``tobytes`` method.
    """

    gen = model.text_to_speech(prompt, voice=voice)
    while True:
        result = await asyncio.to_thread(lambda: next(gen, None))
        if result is None:
            break
        if isinstance(result, tuple) and len(result) == 2:
            _sr, chunk = result
            data = chunk.tobytes() if hasattr(chunk, "tobytes") else chunk
        else:
            data = result
        yield bytes(data)


class TTSAdapter(TTSAdapterProtocol):
    """Concrete adapter that streams PCM audio from a local Llama.cpp model."""

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

