import os
import tempfile
import unittest

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockAngles, ClockState
from analog_clock_app.domain.time.factory import TimeSourceFactory
from analog_clock_app.domain.time.realtime_source import RealTimeSource
from analog_clock_app.domain.time.simulated_source import SimulatedTimeSource
from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import CachedSettingsRepositoryProxy, SQLiteSettingsRepository
from analog_clock_app.presentation.tk_renderer import CenterDotDecorator, ShadowLayerDecorator, TkBaseClockRenderer
from analog_clock_app.services.clock_service import ClockService
from analog_clock_app.services.facade import AppFacade
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.preset_service import PresetService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService
from analog_clock_app.persistence.repositories import SQLitePresetRepository


class TestFactoryMethod(unittest.TestCase):
    def test_factory_real_time(self) -> None:
        settings = AppSettings(time_mode="real")
        source = TimeSourceFactory.create(settings)
        self.assertIsInstance(source, RealTimeSource)

    def test_factory_simulated_time(self) -> None:
        settings = AppSettings(time_mode="simulated", simulation_speed=3.0, time_offset_seconds=60)
        source = TimeSourceFactory.create(settings)
        self.assertIsInstance(source, SimulatedTimeSource)


class TestProxyRepository(unittest.TestCase):
    def test_cached_proxy_updates_cache_on_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "app.db")
            repo = SQLiteSettingsRepository(Database(db_path))
            proxy = CachedSettingsRepositoryProxy(repo)

            s1 = proxy.get_settings()
            self.assertEqual(s1.time_mode, "real")

            updated = AppSettings(time_mode="simulated", simulation_speed=2.0)
            proxy.save_settings(updated)
            s2 = proxy.get_settings()
            self.assertEqual(s2.time_mode, "simulated")
            self.assertEqual(s2.simulation_speed, 2.0)


class FakeCanvas:
    def __init__(self) -> None:
        self.ovals: int = 0
        self.lines: int = 0
        self.bg: str | None = None

    def delete(self, tag: str) -> None:
        return None

    def configure(self, **kwargs) -> None:
        self.bg = kwargs.get("bg", self.bg)

    def create_oval(self, *args, **kwargs) -> int:
        self.ovals += 1
        return self.ovals

    def create_line(self, *args, **kwargs) -> int:
        self.lines += 1
        return self.lines

    def create_arc(self, *args, **kwargs) -> int:
        return 0


class TestDecoratorAndBridge(unittest.TestCase):
    def test_renderer_decorators_draw_extra_layers(self) -> None:
        canvas = FakeCanvas()
        base = TkBaseClockRenderer()
        renderer = CenterDotDecorator(ShadowLayerDecorator(base))
        settings = AppSettings(enable_shadow_layer=True, enable_center_dot_layer=True)
        state = ClockState(angles=ClockAngles(hour=0.0, minute=0.0, second=0.0), ticks=tuple())
        renderer.render(canvas, state, settings, size=320)
        self.assertGreaterEqual(canvas.ovals, 2)


class TestFacade(unittest.TestCase):
    def test_facade_applies_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "app.db")
            db = Database(db_path)

            settings_repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
            presets_repo = SQLitePresetRepository(db)
            settings_service = SettingsService(settings_repo)
            preset_service = PresetService(presets=presets_repo, settings=settings_repo)

            from analog_clock_app.domain.clock.engine import ClockEngine

            engine = ClockEngine()
            clock_service = ClockService(engine=engine, settings_repo=settings_repo)
            history = HistoryService()

            facade = AppFacade(
                clock_service=clock_service,
                settings_service=settings_service,
                preset_service=preset_service,
                history=history,
            )

            updated = facade.apply_settings_patch(SettingsPatch(time_mode="simulated"), "Test")
            self.assertEqual(updated.time_mode, "simulated")


if __name__ == "__main__":
    unittest.main()

