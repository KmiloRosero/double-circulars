from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ClockAngles:
    """Angles for the clock hands, expressed in degrees.

    The 0-degree reference is the 12 o'clock direction, increasing clockwise.
    """

    hour: float
    minute: float
    second: float


TickKind = Literal["major", "minor"]


@dataclass(frozen=True, slots=True)
class TickMark:
    index: int
    angle: float
    kind: TickKind


@dataclass(frozen=True, slots=True)
class ClockState:
    """Domain state required to render an analog clock."""

    angles: ClockAngles
    ticks: tuple[TickMark, ...]

