from datetime import datetime, timezone

from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.domain.time.interfaces import TimeInstant, TimeSource
from analog_clock_app.services.clock_service import ClockService


class FakeTimeSource(TimeSource):
    def __init__(self, dt_utc: datetime) -> None:
        self._instant = TimeInstant(dt_utc=dt_utc)

    def now(self) -> TimeInstant:
        return self._instant


def test_angles_known_time() -> None:
    engine = ClockEngine()
    dt = datetime(2020, 1, 1, 3, 15, 30, tzinfo=timezone.utc)
    state = engine.state_from_datetime(dt)

    assert state.angles.second == 180.0
    assert abs(state.angles.minute - 93.0) < 1e-9
    assert abs(state.angles.hour - 97.75) < 1e-9


def test_major_ticks() -> None:
    engine = ClockEngine()
    dt = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    full = engine.state_from_datetime(dt, major_ticks_only=False)
    major_only = engine.state_from_datetime(dt, major_ticks_only=True)

    assert len(full.ticks) == 60
    assert sum(1 for t in full.ticks if t.kind == "major") == 12
    assert len(major_only.ticks) == 12
    assert all(t.kind == "major" for t in major_only.ticks)


def test_payload_time_source() -> None:
    engine = ClockEngine()
    dt = datetime(2020, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    payload = engine.payload_from_time_source(FakeTimeSource(dt))

    assert set(payload.keys()) == {"angles", "ticks"}
    assert set(payload["angles"].keys()) == {"hour", "minute", "second"}
    assert isinstance(payload["ticks"], list)


def test_timezone_bogota_conversion() -> None:
    dt_utc = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    local = ClockService._to_local_time(dt_utc, "America/Bogota")
    assert local.hour == 7
