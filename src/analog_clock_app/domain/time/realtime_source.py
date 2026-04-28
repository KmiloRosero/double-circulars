from __future__ import annotations

from .interfaces import TimeInstant, TimeSource


class RealTimeSource(TimeSource):
    """Time source that uses the system clock."""

    def now(self) -> TimeInstant:
        return TimeInstant.now_utc()

