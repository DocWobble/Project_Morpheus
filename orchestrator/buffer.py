"""Playback buffer tracking utilities.

The orchestrator treats playback as the clock and attempts to keep the
buffer depth within a comfortable range.  This module provides a simple
mutable object to track buffer occupancy in milliseconds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class PlaybackBuffer:
    """Tracks how much audio is queued for playback.

    Parameters
    ----------
    capacity_ms:
        Maximum desired buffer depth in milliseconds.  The buffer does
        not enforce this strictly but exposes metrics for the
        orchestrator's controller to act on.
    """

    capacity_ms: float
    depth_ms: float = 0.0

    def add(self, duration_ms: float) -> None:
        """Record newly produced audio."""
        self.depth_ms += duration_ms

    def consume(self, duration_ms: float) -> None:
        """Record that audio has been played back."""
        self.depth_ms = max(0.0, self.depth_ms - duration_ms)

    def reset(self) -> None:
        """Flush the buffer, typically after a barge-in event."""
        self.depth_ms = 0.0

    def within(self, band: Tuple[float, float]) -> bool:
        """Return ``True`` if current depth lies inside ``band``."""
        low, high = band
        return low <= self.depth_ms <= high
