from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TimeInstant:
    """An immutable point in time in UTC."""

    dt_utc: datetime

    @staticmethod
    def now_utc() -> "TimeInstant":
        return TimeInstant(dt_utc=datetime.now(timezone.utc))


class TimeSource(Protocol):
    """A source that provides the current time instant."""

    def now(self) -> TimeInstant: ...

