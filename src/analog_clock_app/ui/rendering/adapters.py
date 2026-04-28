from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.domain.clock.models import ClockState


@dataclass(frozen=True, slots=True)
class ClockStateDto:
    """A JSON-friendly representation of clock state."""

    hour_angle: float
    minute_angle: float
    second_angle: float
    ticks: list[dict[str, float | int | str]]


class ClockStateDtoAdapter:
    """Adapter that converts domain models into DTOs suitable for an API/UI."""

    @staticmethod
    def to_dto(state: ClockState) -> ClockStateDto:
        return ClockStateDto(
            hour_angle=state.angles.hour,
            minute_angle=state.angles.minute,
            second_angle=state.angles.second,
            ticks=[{"index": t.index, "angle": t.angle, "kind": t.kind} for t in state.ticks],
        )

