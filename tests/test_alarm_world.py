import os
import tempfile
import unittest
from datetime import datetime, timezone

from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import (
    SQLiteAlarmRepository,
    SQLiteWorldClockRepository,
)
from analog_clock_app.services.alarm_service import AlarmService
from analog_clock_app.services.world_clock_service import WorldClockService


class TestAlarmAndWorldClock(unittest.TestCase):
    def test_alarm_trigger_once_per_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(os.path.join(tmp, "app.db"))
            repo = SQLiteAlarmRepository(db)
            service = AlarmService(repo)

            alarm = service.add_alarm(label="Test", hour=7, minute=0, timezone="America/Bogota")
            now_utc = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

            due1 = service.check_due(now_utc)
            self.assertEqual(len(due1), 1)

            due2 = service.check_due(now_utc)
            self.assertEqual(len(due2), 0)

    def test_world_clock_favorites_crud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(os.path.join(tmp, "app.db"))
            repo = SQLiteWorldClockRepository(db)
            service = WorldClockService(repo)

            fav = service.add_favorite("Pasto, Colombia", "America/Bogota")
            all_fav = service.list_favorites()
            self.assertEqual(len(all_fav), 1)
            self.assertEqual(all_fav[0].label, "Pasto, Colombia")

            service.delete_favorite(fav.id)
            self.assertEqual(service.list_favorites(), [])


if __name__ == "__main__":
    unittest.main()

