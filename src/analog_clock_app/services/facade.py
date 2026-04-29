from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState

from .clock_service import ClockService
from .history_service import HistoryService
from .preset_service import PresetService
from .settings_service import SettingsPatch, SettingsService


@dataclass(slots=True)
class AppFacade:
    """Facade for the UI layer.

    Provides a small API surface for retrieving clock state and managing settings.
    """

    clock_service: ClockService
    settings_service: SettingsService
    preset_service: PresetService
    history: HistoryService

    def get_clock_state(self) -> ClockState:
        return self.clock_service.get_state()

    def get_settings(self) -> AppSettings:
        return self.settings_service.get()

    def apply_settings_patch(self, patch: SettingsPatch, label: str) -> AppSettings:
        before = self.settings_service.get()
        after = self.settings_service.apply_patch(patch)
        self.history.record_change(before, after, label)
        return after

    def undo_settings(self) -> AppSettings | None:
        current = self.settings_service.get()
        if not self.history.can_undo():
            return None
        previous = self.history.undo(current)
        self.settings_service.save(previous)
        return previous

    def redo_settings(self) -> AppSettings | None:
        current = self.settings_service.get()
        if not self.history.can_redo():
            return None
        nxt = self.history.redo(current)
        self.settings_service.save(nxt)
        return nxt

