from __future__ import annotations

from datetime import datetime, timedelta, timezone

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.domain.clock.models import ClockState
from analog_clock_app.domain.time.factory import TimeSourceFactory
from analog_clock_app.persistence.repositories import SettingsRepository


class ClockService:
    """Application service to produce clock state."""

    def __init__(self, engine: ClockEngine, settings_repo: SettingsRepository) -> None:
        self._engine = engine
        self._settings_repo = settings_repo

    def get_state(self) -> ClockState:
        settings = self._settings_repo.get_settings()
        time_source = TimeSourceFactory.create(settings)
        instant = time_source.now()
        local_dt = self._to_local_time(instant.dt_utc, settings.timezone)
        return self._engine.state_from_datetime(local_dt, major_ticks_only=settings.show_major_ticks_only)

    @staticmethod
    def _to_local_time(dt_utc: datetime, tz_name: str) -> datetime:
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)

        normalized = (tz_name or "").strip()

        if normalized.lower() in {"america/bogota", "colombia", "pasto", "pasto/colombia"}:
            bogota_tz = timezone(timedelta(hours=-5), name="America/Bogota")
            return dt_utc.astimezone(bogota_tz)

        try:
            from zoneinfo import ZoneInfo

            return dt_utc.astimezone(ZoneInfo(normalized))
        except Exception:
            return dt_utc

