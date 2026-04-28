from __future__ import annotations

from analog_clock_app.config.settings import AppSettings

from .interfaces import TimeSource
from .realtime_source import RealTimeSource
from .simulated_source import SimulatedTimeSource


class TimeSourceFactory:
    """Factory Method for creating the active time source based on settings."""

    @staticmethod
    def create(settings: AppSettings) -> TimeSource:
        if settings.time_mode == "simulated":
            return SimulatedTimeSource(
                speed=settings.simulation_speed,
                offset_seconds=settings.time_offset_seconds,
            )
        return RealTimeSource()

