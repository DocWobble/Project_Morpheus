"""Discrete chunk-size ladder used by the adaptive rate controller."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

DEFAULT_LADDER: List[int] = [8, 12, 16, 24, 32, 48, 64]


@dataclass
class ChunkLadder:
    """Manage step-wise chunk size selection.

    The controller can step up or down the ladder in response to playback
    buffer signals.  Ladder values are expressed in adapter native units
    (tokens for text-based models or milliseconds for waveform models).
    """

    ladder: List[int] = field(default_factory=lambda: DEFAULT_LADDER.copy())
    index: int = 0

    @property
    def current(self) -> int:
        return self.ladder[self.index]

    def step_up(self) -> None:
        if self.index < len(self.ladder) - 1:
            self.index += 1

    def step_down(self) -> None:
        if self.index > 0:
            self.index -= 1

    def reset(self) -> None:
        self.index = 0

    def adapt(self, depth_ms: float, band: Tuple[float, float]) -> None:
        """Adjust ladder position based on ``depth_ms``.

        ``band`` defines the low and high water marks of the playback
        buffer.  If the buffer is shallow we step up to request larger
        chunks; if it is too deep we step down to ease backpressure.
        """
        low, high = band
        if depth_ms < low:
            self.step_up()
        elif depth_ms > high:
            self.step_down()
