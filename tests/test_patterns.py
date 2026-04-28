import os
import tempfile
import unittest

from datetime import datetime, timezone

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.domain.time.factory import TimeSourceFactory
from analog_clock_app.domain.time.realtime_source import RealTimeSource
from analog_clock_app.domain.time.simulated_source import SimulatedTimeSource
from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import (
    CachedSettingsRepositoryProxy,
    SQLiteSettingsRepository,
)
from analog_clock_app.services.clock_service import ClockService
from analog_clock_app.services.facade import ClockFacade
from analog_clock_app.ui.presenter import ClockPresenter
from analog_clock_app.ui.rendering.decorators import CenterDotDecorator, ShadowLayerDecorator
from analog_clock_app.ui.rendering.svg_renderer import SvgClockRenderer


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


class TestDecoratorAndBridge(unittest.TestCase):
    def test_renderer_decorators(self) -> None:
        engine = ClockEngine()
        state = engine.state_from_datetime(datetime.now(timezone.utc))

        base = SvgClockRenderer()
        renderer = CenterDotDecorator(ShadowLayerDecorator(base))
        settings = AppSettings(enable_shadow_layer=True, enable_center_dot_layer=True)
        svg = renderer.render(state, settings)
        self.assertIn("<svg", svg)
        self.assertIn("filter=\"url(#shadow)\"", svg)
        self.assertIn("<circle", svg)

    def test_bridge_presenter_renders_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "app.db")
            repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(Database(db_path)))
            engine = ClockEngine()
            service = ClockService(engine=engine, settings_repo=repo)
            renderer = CenterDotDecorator(SvgClockRenderer())

            presenter = ClockPresenter(clock_service=service, renderer=renderer)
            settings = repo.get_settings()
            svg = presenter.render(settings)
            self.assertIn("<svg", svg)


class TestFacade(unittest.TestCase):
    def test_facade_renders_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "app.db")
            repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(Database(db_path)))
            engine = ClockEngine()
            service = ClockService(engine=engine, settings_repo=repo)
            renderer = SvgClockRenderer()
            facade = ClockFacade(clock_service=service, settings_repo=repo, renderer=renderer)
            svg = facade.render_clock_svg()
            self.assertIn("<svg", svg)


if __name__ == "__main__":
    unittest.main()

