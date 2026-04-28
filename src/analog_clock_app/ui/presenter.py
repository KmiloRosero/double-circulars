from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState
from analog_clock_app.services.clock_service import ClockService

from .rendering.interfaces import ClockRenderer


@dataclass(slots=True)
class ClockPresenter:
    """Bridge abstraction that connects services to a renderer.

    The UI can depend on this class without needing to know how the clock state is
    computed (engine + time source) or how it is rendered (SVG + decorators).
    """

    clock_service: ClockService
    renderer: ClockRenderer

    def get_state(self) -> ClockState:
        return self.clock_service.get_state()

    def render(self, settings: AppSettings) -> str:
        state = self.get_state()
        return self.renderer.render(state, settings)

