from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from analog_clock_app.persistence.repositories import Alarm, AlarmRepository
from analog_clock_app.services.clock_service import ClockService


@dataclass(slots=True)
class AlarmService:
    """Service layer for alarms.

    Alarms are daily alarms in a specific timezone, identified by hour/minute.
    The service marks alarms as triggered per local date to avoid repeated
    triggers within the same day.
    """

    repo: AlarmRepository

    def list_alarms(self) -> list[Alarm]:
        return self.repo.list_alarms()

    def add_alarm(self, label: str, hour: int, minute: int, timezone: str) -> Alarm:
        return self.repo.add_alarm(label=label, hour=hour, minute=minute, timezone=timezone)

    def set_enabled(self, alarm_id: str, enabled: bool) -> None:
        self.repo.set_enabled(alarm_id, enabled)

    def delete_alarm(self, alarm_id: str) -> None:
        self.repo.delete_alarm(alarm_id)

    def check_due(self, now_utc: datetime) -> list[Alarm]:
        triggered: list[Alarm] = []
        for alarm in self.repo.list_alarms():
            if not alarm.enabled:
                continue

            local_now = ClockService._to_local_time(now_utc, alarm.timezone)
            local_date = local_now.date().isoformat()

            if alarm.last_triggered_local_date == local_date:
                continue

            if local_now.hour == alarm.hour and local_now.minute == alarm.minute:
                self.repo.mark_triggered(alarm.id, local_date)
                triggered.append(
                    Alarm(
                        id=alarm.id,
                        label=alarm.label,
                        hour=alarm.hour,
                        minute=alarm.minute,
                        enabled=alarm.enabled,
                        timezone=alarm.timezone,
                        last_triggered_local_date=local_date,
                    )
                )
        return triggered

