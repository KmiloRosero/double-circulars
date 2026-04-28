import unittest
from datetime import datetime, timezone

from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.domain.time.interfaces import TimeInstant, TimeSource


class FakeTimeSource(TimeSource):
    def __init__(self, dt_utc: datetime) -> None:
        self._instant = TimeInstant(dt_utc=dt_utc)

    def now(self) -> TimeInstant:
        return self._instant


class TestClockEngine(unittest.TestCase):
    def test_angles_known_time(self) -> None:
        engine = ClockEngine()
        dt = datetime(2020, 1, 1, 3, 15, 30, tzinfo=timezone.utc)
        state = engine.state_from_datetime(dt)

        self.assertAlmostEqual(state.angles.second, 180.0, places=6)
        self.assertAlmostEqual(state.angles.minute, 93.0, places=6)
        self.assertAlmostEqual(state.angles.hour, 97.75, places=6)

    def test_ticks_full_and_major_only(self) -> None:
        engine = ClockEngine()
        dt = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        full = engine.state_from_datetime(dt, major_ticks_only=False)
        self.assertEqual(len(full.ticks), 60)
        self.assertEqual(sum(1 for t in full.ticks if t.kind == "major"), 12)

        major_only = engine.state_from_datetime(dt, major_ticks_only=True)
        self.assertEqual(len(major_only.ticks), 12)
        self.assertTrue(all(t.kind == "major" for t in major_only.ticks))

    def test_payload_json_friendly(self) -> None:
        engine = ClockEngine()
        dt = datetime(2020, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
        payload = engine.payload_from_datetime(dt)

        self.assertIn("angles", payload)
        self.assertIn("ticks", payload)
        self.assertIsInstance(payload["angles"], dict)
        self.assertIsInstance(payload["ticks"], list)
        self.assertIn("hour", payload["angles"])
        self.assertIn("minute", payload["angles"])
        self.assertIn("second", payload["angles"])
        self.assertEqual(len(payload["ticks"]), 60)
        self.assertIsInstance(payload["ticks"][0], dict)

    def test_time_source_integration(self) -> None:
        engine = ClockEngine()
        dt = datetime(2020, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        source = FakeTimeSource(dt)
        payload = engine.payload_from_time_source(source)
        self.assertEqual(len(payload["ticks"]), 60)


if __name__ == "__main__":
    unittest.main()

