from __future__ import annotations

import os
from pathlib import Path

from nicegui import app, ui

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import (
    CachedSettingsRepositoryProxy,
    SQLiteAlarmRepository,
    SQLitePresetRepository,
    SQLiteSettingsRepository,
    SQLiteWorldClockRepository,
)
from analog_clock_app.services.alarm_service import AlarmService
from analog_clock_app.services.clock_service import ClockService
from analog_clock_app.services.facade import ClockFacade
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.preset_service import PresetService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService
from analog_clock_app.services.world_clock_service import WorldClockService
from analog_clock_app.ui.presenter import ClockPresenter
from analog_clock_app.ui.rendering.decorators import CenterDotDecorator, ShadowLayerDecorator
from analog_clock_app.ui.rendering.svg_renderer import SvgClockRenderer

from .pages.about_page import about_page
from .pages.alarms_page import alarms_page
from .pages.clock_page import clock_page
from .pages.settings_page import settings_page
from .pages.stopwatch_page import stopwatch_page
from .pages.timer_page import timer_page
from .pages.world_clock_page import world_clock_page


def _default_db_path() -> str:
    p = os.environ.get("ANALOG_CLOCK_DB")
    if p:
        return p
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "app.db")


def _build_facade() -> tuple[
    ClockFacade,
    SettingsService,
    PresetService,
    AlarmService,
    WorldClockService,
    HistoryService,
    ClockPresenter,
]:
    db = Database(_default_db_path())
    settings_repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
    presets_repo = SQLitePresetRepository(db)
    alarms_repo = SQLiteAlarmRepository(db)
    world_repo = SQLiteWorldClockRepository(db)

    engine = ClockEngine()
    clock_service = ClockService(engine=engine, settings_repo=settings_repo)

    base_renderer = SvgClockRenderer()
    renderer = CenterDotDecorator(ShadowLayerDecorator(base_renderer))

    facade = ClockFacade(clock_service=clock_service, settings_repo=settings_repo, renderer=renderer)
    settings_service = SettingsService(settings_repo)
    preset_service = PresetService(presets=presets_repo, settings=settings_repo)
    alarm_service = AlarmService(alarms_repo)
    world_clock_service = WorldClockService(world_repo)
    history = HistoryService()
    presenter = ClockPresenter(clock_service=clock_service, renderer=renderer)
    return facade, settings_service, preset_service, alarm_service, world_clock_service, history, presenter


def _top_nav() -> None:
    with ui.row().classes("w-full items-center justify-between").style(
        "padding: 12px 16px; border-bottom: 1px solid #E5E7EB;"
    ):
        ui.label("Reloj Analógico").style("font-weight: 700;")
        with ui.row().classes("items-center").style("gap: 10px;"):
            ui.link("Reloj", "/").style("text-decoration: none;")
            ui.link("Alarmas", "/alarmas").style("text-decoration: none;")
            ui.link("Mundial", "/mundial").style("text-decoration: none;")
            ui.link("Cronómetro", "/cronometro").style("text-decoration: none;")
            ui.link("Temporizador", "/temporizador").style("text-decoration: none;")
            ui.link("Configuración", "/settings").style("text-decoration: none;")
            ui.link("Acerca de", "/about").style("text-decoration: none;")


def run() -> None:
    facade, settings_service, preset_service, alarm_service, world_clock_service, history, presenter = _build_facade()

    def _apply_theme() -> None:
        settings = settings_service.get()
        dm = ui.dark_mode()
        if settings.dark_theme:
            dm.enable()
        else:
            dm.disable()

    @ui.page("/")
    def _clock() -> None:
        _apply_theme()
        _top_nav()
        clock_page(
            facade=facade,
            settings_service=settings_service,
            preset_service=preset_service,
            history=history,
            presenter=presenter,
        )

    @ui.page("/alarmas")
    def _alarms() -> None:
        _apply_theme()
        _top_nav()
        alarms_page(settings_service=settings_service, alarm_service=alarm_service, history=history)

    @ui.page("/mundial")
    def _world() -> None:
        _apply_theme()
        _top_nav()
        world_clock_page(
            settings_service=settings_service,
            world_clock_service=world_clock_service,
            history=history,
            renderer=facade.renderer,
        )

    @ui.page("/cronometro")
    def _stopwatch() -> None:
        _apply_theme()
        _top_nav()
        stopwatch_page()

    @ui.page("/temporizador")
    def _timer() -> None:
        _apply_theme()
        _top_nav()
        timer_page()

    @ui.page("/settings")
    def _settings() -> None:
        _apply_theme()
        _top_nav()
        settings_page(
            settings_service=settings_service,
            history=history,
            presenter=presenter,
        )

    @ui.page("/about")
    def _about() -> None:
        _apply_theme()
        _top_nav()
        about_page()

    static_dir = Path.cwd() / "static"
    if static_dir.exists():
        app.add_static_files("/static", str(static_dir), follow_symlink=True)

    storage_secret = os.environ.get("ANALOG_CLOCK_STORAGE_SECRET", "local-dev")
    ui.run(title="Reloj Analógico", port=8080, reload=False, storage_secret=storage_secret)


