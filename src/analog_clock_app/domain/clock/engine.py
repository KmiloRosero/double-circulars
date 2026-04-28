from __future__ import annotations

from datetime import datetime
from typing import Any

from analog_clock_app.domain.structures.doubly_circular_list import DoublyCircularLinkedList
from analog_clock_app.domain.time.interfaces import TimeSource

from .models import ClockAngles, ClockState, TickKind, TickMark


class ClockEngine:
    """Computes analog clock state using a 60-node doubly circular linked list."""

    def __init__(self) -> None:
        self._ticks = DoublyCircularLinkedList(range(60))

    def state_from_datetime(self, dt: datetime, major_ticks_only: bool = False) -> ClockState:
        second = dt.second + (dt.microsecond / 1_000_000.0)
        minute = dt.minute + (second / 60.0)
        hour_12 = (dt.hour % 12) + (minute / 60.0)

        second_angle = (second / 60.0) * 360.0
        minute_angle = (minute / 60.0) * 360.0
        hour_angle = (hour_12 / 12.0) * 360.0

        ticks: list[TickMark] = []
        if self._ticks.head is not None:
            node = self._ticks.head
            for _ in range(self._ticks.size):
                idx = int(node.value)
                is_major = (idx % 5) == 0
                if (not major_ticks_only) or is_major:
                    kind: TickKind = "major" if is_major else "minor"
                    ticks.append(TickMark(index=idx, angle=(idx / 60.0) * 360.0, kind=kind))
                node = node.next

        return ClockState(
            angles=ClockAngles(hour=hour_angle, minute=minute_angle, second=second_angle),
            ticks=tuple(ticks),
        )

    def state_from_time_source(self, time_source: TimeSource, major_ticks_only: bool = False) -> ClockState:
        instant = time_source.now()
        return self.state_from_datetime(instant.dt_utc, major_ticks_only=major_ticks_only)

    def payload_from_datetime(self, dt: datetime, major_ticks_only: bool = False) -> dict[str, Any]:
        state = self.state_from_datetime(dt, major_ticks_only=major_ticks_only)
        return {
            "angles": {
                "hour": state.angles.hour,
                "minute": state.angles.minute,
                "second": state.angles.second,
            },
            "ticks": [
                {"index": t.index, "angle": t.angle, "kind": t.kind}
                for t in state.ticks
            ],
        }

    def payload_from_time_source(self, time_source: TimeSource, major_ticks_only: bool = False) -> dict[str, Any]:
        instant = time_source.now()
        return self.payload_from_datetime(instant.dt_utc, major_ticks_only=major_ticks_only)

