import unittest
from datetime import datetime, timezone

from analog_clock_app.services.clock_service import ClockService


class TestTimezoneConversion(unittest.TestCase):
    def test_bogota_offset(self) -> None:
        dt_utc = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        local = ClockService._to_local_time(dt_utc, "America/Bogota")
        self.assertEqual(local.hour, 7)
        self.assertEqual(local.minute, 0)


if __name__ == "__main__":
    unittest.main()

