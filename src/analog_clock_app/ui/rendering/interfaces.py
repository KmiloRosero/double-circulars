from __future__ import annotations

from typing import Protocol

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState


class ClockRenderer(Protocol):
    """Bridge implementor: converts clock state into a renderable artifact."""

    def render(self, state: ClockState, settings: AppSettings) -> str: ...

