from __future__ import annotations

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.persistence.repositories import Preset, PresetRepository, SettingsRepository


class PresetService:
    """Service layer for presets.

    Presets are snapshots of AppSettings saved in SQLite.
    """

    def __init__(self, presets: PresetRepository, settings: SettingsRepository) -> None:
        self._presets = presets
        self._settings = settings

    def list_presets(self) -> list[Preset]:
        return self._presets.list_presets()

    def save_current_settings_as_preset(self, name: str) -> Preset:
        current = self._settings.get_settings()
        return self._presets.save_preset(name=name, settings=current)

    def apply_preset(self, preset_id: str) -> AppSettings:
        preset = self._presets.get_preset(preset_id)
        self._settings.save_settings(preset.settings)
        return preset.settings

    def delete_preset(self, preset_id: str) -> None:
        self._presets.delete_preset(preset_id)

