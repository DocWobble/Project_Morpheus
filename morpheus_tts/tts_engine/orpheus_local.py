"""Orpheus TTS adapter for local PCM streaming.

This adapter wraps :func:`generate_speech_from_api` and translates its
output into :class:`~morpheus_tts.orchestrator.adapter.AudioChunk`
objects.  The underlying generator may yield PCM segments of arbitrary
size, so we maintain an internal buffer and slice the data to honour the
``chunk_size`` requested by the orchestrator.  ``chunk_size`` is
expressed in milliseconds which is converted to a byte limit based on
the configured sample rate.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional
from importlib import metadata


def _get_orpheuscpp_version() -> str:
    """Return the installed OrpheusCpp version or ``"unknown"``.

    The function is defensive – if the package isn't installed or metadata
    cannot be read, ``"unknown"`` is returned rather than raising.  This keeps
    error messages informative without introducing a hard dependency.
    """

    try:
        return metadata.version("OrpheusCpp")
    except Exception:  # pragma: no cover - best effort only
        return "unknown"


def _set_snac_decoder_session(decoder: object, session: object) -> None:
    """Assign ``session`` to a SNAC decoder with graceful fallback.

    OrpheusCpp has historically exposed the decoder session as a mutable
    attribute (``decoder.session``).  Future versions may instead provide a
    ``set_session`` method or remove direct access entirely.  This helper tries
    both approaches and emits a clear error if neither is available so that
    callers receive actionable feedback rather than an ``AttributeError``.
    """

    if hasattr(decoder, "set_session"):
        decoder.set_session(session)
        return

    if hasattr(decoder, "session"):
        try:
            setattr(decoder, "session", session)
            return
        except Exception as exc:  # pragma: no cover - assignment failed
            raise RuntimeError(
                "OrpheusCpp refuses setting the SNAC decoder session. "
                "Please update to a compatible version."
            ) from exc

    raise RuntimeError(
        "Installed OrpheusCpp %s lacks a supported API to configure the "
        "SNAC decoder session." % _get_orpheuscpp_version()
    )

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
        snac_decoder: Optional[object] = None,
        snac_session: Optional[object] = None,
    ) -> None:
        self.prompt = prompt
        self.voice = voice
        self.use_batching = use_batching
        self.max_batch_chars = max_batch_chars
        self._gen: Optional[AsyncGenerator[bytes, None]] = None
        self._buffer = bytearray()
        self._exhausted = False

        # When running fully locally with OrpheusCpp we may need to manually
        # bind a decoder session.  Older releases required direct attribute
        # assignment (``decoder.session``) which breaks when the attribute is
        # removed.  By funnelling the operation through a helper we can detect
        # unsupported versions early and emit an actionable error message.
        if snac_decoder is not None and snac_session is not None:
            _set_snac_decoder_session(snac_decoder, snac_session)

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
            Desired chunk duration in milliseconds.  The adapter slices
            the PCM stream so that the returned ``AudioChunk`` never
            exceeds this duration.
        """

        target_bytes = int(chunk_size / 1000 * SAMPLE_RATE * 2)

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

