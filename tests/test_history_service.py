import unittest

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.services.history_service import HistoryService


class TestHistoryService(unittest.TestCase):
    def test_undo_redo_flow(self) -> None:
        history = HistoryService(max_events=10)

        s1 = AppSettings(time_mode="real", simulation_speed=1.0)
        s2 = AppSettings(time_mode="simulated", simulation_speed=2.0)
        s3 = AppSettings(time_mode="simulated", simulation_speed=3.0)

        history.record_change(s1, s2, "Change 1")
        history.record_change(s2, s3, "Change 2")

        self.assertTrue(history.can_undo())
        self.assertFalse(history.can_redo())

        cur = s3
        cur = history.undo(cur)
        self.assertEqual(cur.simulation_speed, 2.0)
        self.assertTrue(history.can_redo())

        cur = history.redo(cur)
        self.assertEqual(cur.simulation_speed, 3.0)

    def test_event_log_is_bounded(self) -> None:
        history = HistoryService(max_events=3)
        base = AppSettings()

        history.record_change(base, base, "A")
        history.record_change(base, base, "B")
        history.record_change(base, base, "C")
        history.record_change(base, base, "D")

        events = history.events()
        self.assertEqual(events, ["B", "C", "D"])


if __name__ == "__main__":
    unittest.main()

