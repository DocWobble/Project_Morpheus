"""Byte-oriented ring buffer for PCM streaming.

The ring buffer stores raw PCM bytes and optionally updates a
``PlaybackBuffer`` instance so the orchestrator can track how much audio
is queued for playback.  Both write and read operations are expressed in
bytes; the buffer converts between byte counts and milliseconds using a
fixed sample rate of 16-bit mono PCM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .buffer import PlaybackBuffer

BYTES_PER_SAMPLE = 2  # PCM16 mono


def _bytes_to_ms(n: int, sample_rate: int) -> float:
    """Convert ``n`` PCM bytes to milliseconds."""
    if sample_rate <= 0:
        return 0.0
    samples = n / BYTES_PER_SAMPLE
    return samples / sample_rate * 1000.0


@dataclass
class RingBuffer:
    """Simple circular buffer that tracks playback consumption."""

    capacity: int
    sample_rate: int
    playback: Optional[PlaybackBuffer] = None

    def __post_init__(self) -> None:
        self._buf = bytearray(self.capacity)
        self._read = 0
        self._write = 0
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def write(self, data: bytes) -> int:
        """Append ``data`` to the buffer.

        Returns the number of bytes written which may be less than the
        length of ``data`` if the buffer is full.
        """
        if not data:
            return 0
        space = self.capacity - self._size
        n = min(len(data), space)
        first = min(n, self.capacity - self._write)
        self._buf[self._write : self._write + first] = data[:first]
        second = n - first
        if second:
            self._buf[0:second] = data[first:first + second]
        self._write = (self._write + n) % self.capacity
        self._size += n
        if self.playback:
            self.playback.add(_bytes_to_ms(n, self.sample_rate))
        return n

    def read(self, size: int) -> bytes:
        """Remove and return up to ``size`` bytes from the buffer."""
        if size <= 0 or self._size == 0:
            return b""
        n = min(size, self._size)
        first = min(n, self.capacity - self._read)
        data = bytes(self._buf[self._read : self._read + first])
        second = n - first
        if second:
            data += bytes(self._buf[0:second])
        self._read = (self._read + n) % self.capacity
        self._size -= n
        if self.playback:
            self.playback.consume(_bytes_to_ms(n, self.sample_rate))
        return data

    def reset(self) -> None:
        """Flush all buffered audio."""
        self._read = self._write = self._size = 0
