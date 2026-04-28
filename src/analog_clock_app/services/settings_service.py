from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.config.settings import BackgroundMode, TimeMode
from analog_clock_app.persistence.repositories import SettingsRepository


@dataclass(frozen=True, slots=True)
class SettingsPatch:
    """Partial update for AppSettings."""

    time_mode: Optional[TimeMode] = None
    simulation_speed: Optional[float] = None
    time_offset_seconds: Optional[int] = None

    face_color: Optional[str] = None
    tick_color: Optional[str] = None
    hand_color: Optional[str] = None

    show_major_ticks_only: Optional[bool] = None
    enable_shadow_layer: Optional[bool] = None
    enable_center_dot_layer: Optional[bool] = None

    dark_theme: Optional[bool] = None

    background_mode: Optional[BackgroundMode] = None
    background_image_filename: Optional[str] = None


class SettingsService:
    """Service layer for managing settings lifecycle."""

    def __init__(self, repo: SettingsRepository) -> None:
        self._repo = repo

    def get(self) -> AppSettings:
        return self._repo.get_settings()

    def save(self, settings: AppSettings) -> None:
        self._repo.save_settings(settings)

    def apply_patch(self, patch: SettingsPatch) -> AppSettings:
        current = self.get()
        updated = replace(
            current,
            time_mode=patch.time_mode if patch.time_mode is not None else current.time_mode,
            simulation_speed=(
                patch.simulation_speed if patch.simulation_speed is not None else current.simulation_speed
            ),
            time_offset_seconds=(
                patch.time_offset_seconds
                if patch.time_offset_seconds is not None
                else current.time_offset_seconds
            ),
            face_color=patch.face_color if patch.face_color is not None else current.face_color,
            tick_color=patch.tick_color if patch.tick_color is not None else current.tick_color,
            hand_color=patch.hand_color if patch.hand_color is not None else current.hand_color,
            show_major_ticks_only=(
                patch.show_major_ticks_only
                if patch.show_major_ticks_only is not None
                else current.show_major_ticks_only
            ),
            enable_shadow_layer=(
                patch.enable_shadow_layer
                if patch.enable_shadow_layer is not None
                else current.enable_shadow_layer
            ),
            enable_center_dot_layer=(
                patch.enable_center_dot_layer
                if patch.enable_center_dot_layer is not None
                else current.enable_center_dot_layer
            ),
            dark_theme=patch.dark_theme if patch.dark_theme is not None else current.dark_theme,
            background_mode=(
                patch.background_mode if patch.background_mode is not None else current.background_mode
            ),
            background_image_filename=(
                patch.background_image_filename
                if patch.background_image_filename is not None
                else current.background_image_filename
            ),
        )
        self.save(updated)
        return updated

