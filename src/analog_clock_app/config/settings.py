from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TimeMode = Literal["real", "simulated"]
BackgroundMode = Literal["white", "black", "image"]


@dataclass(slots=True)
class AppSettings:
    """User-configurable settings for the analog clock app."""

    timezone: str = "America/Bogota"

    dark_theme: bool = False

    background_mode: BackgroundMode = "white"
    background_image_filename: str = ""

    time_mode: TimeMode = "real"
    simulation_speed: float = 1.0
    time_offset_seconds: int = 0

    face_color: str = "#111827"
    tick_color: str = "#E5E7EB"
    hand_color: str = "#F9FAFB"

    show_major_ticks_only: bool = False
    enable_shadow_layer: bool = True
    enable_center_dot_layer: bool = True

