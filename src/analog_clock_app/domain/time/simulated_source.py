from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .interfaces import TimeInstant, TimeSource


@dataclass(slots=True)
class SimulatedTimeSource(TimeSource):
    """Time source that simulates time based on a speed factor and offset.

    The simulation is deterministic relative to a real-time anchor.
    """

    speed: float
    offset_seconds: int
    _anchor_real: TimeInstant
    _anchor_simulated: TimeInstant

    def __init__(self, speed: float, offset_seconds: int) -> None:
        self.speed = speed
        self.offset_seconds = offset_seconds
        self._anchor_real = TimeInstant.now_utc()
        base = self._anchor_real.dt_utc + timedelta(seconds=offset_seconds)
        self._anchor_simulated = TimeInstant(dt_utc=base)

    def now(self) -> TimeInstant:
        real_now = TimeInstant.now_utc().dt_utc
        delta_real = real_now - self._anchor_real.dt_utc
        scaled = timedelta(seconds=delta_real.total_seconds() * self.speed)
        return TimeInstant(dt_utc=self._anchor_simulated.dt_utc + scaled)

