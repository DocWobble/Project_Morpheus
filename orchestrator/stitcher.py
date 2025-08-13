"""Overlap-add stitcher for adapter chunks."""
from __future__ import annotations

from typing import AsyncIterator, AsyncGenerator
import numpy as np

from .adapter import AudioChunk


async def stitch_chunks(
    chunks: AsyncIterator[AudioChunk],
    *,
    sample_rate: int,
    overlap_ms: float = 0.0,
    emit_markers: bool = False,
) -> AsyncGenerator[AudioChunk, None]:
    """Join ``chunks`` using overlap-add with optional marker propagation.

    Parameters
    ----------
    chunks:
        Asynchronous iterator yielding ``AudioChunk`` instances.
    sample_rate:
        PCM sampling rate in Hz.
    overlap_ms:
        Desired crossfade overlap in milliseconds.  The stitcher keeps the
        last ``overlap_ms`` of each chunk and mixes it with the head of the
        next chunk using linear fade in/out.  Drift guard ensures we never
        overlap more samples than are available.
    emit_markers:
        When ``True`` any marker payload on input chunks is forwarded to the
        output.  Otherwise markers are suppressed.
    """

    tail = np.zeros(0, dtype=np.int16)
    overlap_samples = int(overlap_ms * sample_rate / 1000.0)

    async for chunk in chunks:
        pcm = np.frombuffer(chunk.pcm, dtype=np.int16)
        if tail.size:
            if overlap_samples > 0:
                ov = min(overlap_samples, tail.size, pcm.size)
                if ov:
                    fade_out = tail[-ov:] * np.linspace(1.0, 0.0, ov, endpoint=False)
                    fade_in = pcm[:ov] * np.linspace(0.0, 1.0, ov, endpoint=False)
                    pcm = np.concatenate([tail[:-ov], fade_out + fade_in, pcm[ov:]])
                else:
                    pcm = np.concatenate([tail, pcm])
            else:
                pcm = np.concatenate([tail, pcm])
        if chunk.eos:
            duration_ms = len(pcm) / sample_rate * 1000.0
            markers = chunk.markers if emit_markers else None
            yield AudioChunk(
                pcm=pcm.astype('<i2').tobytes(),
                duration_ms=duration_ms,
                markers=markers,
                eos=True,
            )
            tail = np.zeros(0, dtype=np.int16)
            break
        if overlap_samples > 0:
            if pcm.size <= overlap_samples:
                # not enough to emit; accumulate into tail
                tail = pcm
                continue
            out = pcm[:-overlap_samples]
            tail = pcm[-overlap_samples:]
        else:
            out = pcm
            tail = np.zeros(0, dtype=np.int16)
        duration_ms = len(out) / sample_rate * 1000.0
        markers = chunk.markers if emit_markers else None
        yield AudioChunk(pcm=out.astype('<i2').tobytes(), duration_ms=duration_ms, markers=markers, eos=False)

    # If stream ended without explicit EOS, flush remaining tail
    if tail.size:
        duration_ms = len(tail) / sample_rate * 1000.0
        yield AudioChunk(pcm=tail.astype('<i2').tobytes(), duration_ms=duration_ms, markers=None, eos=True)
