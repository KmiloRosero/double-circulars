from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState
from analog_clock_app.persistence.repositories import SettingsRepository
from analog_clock_app.ui.rendering.interfaces import ClockRenderer

from .clock_service import ClockService


@dataclass(slots=True)
class ClockFacade:
    """Facade that provides a small, UI-friendly API surface."""

    clock_service: ClockService
    settings_repo: SettingsRepository
    renderer: ClockRenderer

    def get_settings(self) -> AppSettings:
        return self.settings_repo.get_settings()

    def save_settings(self, settings: AppSettings) -> None:
        self.settings_repo.save_settings(settings)

    def get_clock_state(self) -> ClockState:
        return self.clock_service.get_state()

    def render_clock_svg(self) -> str:
        settings = self.get_settings()
        state = self.get_clock_state()
        return self.renderer.render(state, settings)

