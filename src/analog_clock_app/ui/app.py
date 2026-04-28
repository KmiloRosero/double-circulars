from __future__ import annotations

import os
from pathlib import Path
import time

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


def _uploads_dir() -> Path:
    p = Path.cwd() / "data" / "uploads"
    p.mkdir(parents=True, exist_ok=True)
    return p


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

    def _apply_theme_and_background() -> None:
        settings = settings_service.get()
        dm = ui.dark_mode()
        if settings.dark_theme:
            dm.enable()
        else:
            dm.disable()

        if settings.background_mode == "black":
            js = (
                "document.body.style.backgroundColor = '#000000';"
                "document.body.style.backgroundImage = 'none';"
                "document.body.style.backgroundSize = '';"
                "document.body.style.backgroundRepeat = '';"
                "document.body.style.backgroundPosition = '';"
            )
            ui.run_javascript(js)
        elif settings.background_mode == "image" and settings.background_image_filename:
            ts = int(time.time())
            url = f"/userfiles/{settings.background_image_filename}?t={ts}"
            js = (
                "document.body.style.backgroundColor = '#000000';"
                f"document.body.style.backgroundImage = 'url({url})';"
                "document.body.style.backgroundSize = 'cover';"
                "document.body.style.backgroundRepeat = 'no-repeat';"
                "document.body.style.backgroundPosition = 'center center';"
            )
            ui.run_javascript(js)
        else:
            js = (
                "document.body.style.backgroundColor = '#ffffff';"
                "document.body.style.backgroundImage = 'none';"
                "document.body.style.backgroundSize = '';"
                "document.body.style.backgroundRepeat = '';"
                "document.body.style.backgroundPosition = '';"
            )
            ui.run_javascript(js)

    def _top_header() -> None:
        with ui.row().classes("w-full items-center justify-between").style(
            "padding: 12px 16px; border-bottom: 1px solid #E5E7EB;"
        ):
            ui.label("Reloj Analógico").style("font-weight: 700;")
            ui.label("Pasto, Colombia").style("opacity: 0.8;")

    @ui.page("/")
    def _single_tab_app() -> None:
        _apply_theme_and_background()
        _top_header()

        with ui.column().style("max-width: 1200px; margin: 0 auto; padding: 16px;"):
            tabs = ui.tabs().classes("w-full")
            with tabs:
                ui.tab("Reloj")
                ui.tab("Alarmas")
                ui.tab("Mundial")
                ui.tab("Cronómetro")
                ui.tab("Temporizador")
                ui.tab("Configuración")
                ui.tab("Acerca de")

            with ui.tab_panels(tabs, value="Reloj").classes("w-full"):
                with ui.tab_panel("Reloj"):
                    clock_page(
                        facade=facade,
                        settings_service=settings_service,
                        preset_service=preset_service,
                        history=history,
                        presenter=presenter,
                    )

                with ui.tab_panel("Alarmas"):
                    alarms_page(
                        settings_service=settings_service,
                        alarm_service=alarm_service,
                        history=history,
                    )

                with ui.tab_panel("Mundial"):
                    world_clock_page(
                        settings_service=settings_service,
                        world_clock_service=world_clock_service,
                        history=history,
                        renderer=facade.renderer,
                    )

                with ui.tab_panel("Cronómetro"):
                    stopwatch_page()

                with ui.tab_panel("Temporizador"):
                    timer_page()

                with ui.tab_panel("Configuración"):
                    settings_page(
                        settings_service=settings_service,
                        history=history,
                        presenter=presenter,
                        on_settings_changed=_apply_theme_and_background,
                    )

                with ui.tab_panel("Acerca de"):
                    about_page()

    static_dir = Path.cwd() / "static"
    if static_dir.exists():
        app.add_static_files("/static", str(static_dir), follow_symlink=True)

    app.add_static_files("/userfiles", str(_uploads_dir()), follow_symlink=True)

    storage_secret = os.environ.get("ANALOG_CLOCK_STORAGE_SECRET", "local-dev")
    ui.run(title="Reloj Analógico", port=8080, reload=False, storage_secret=storage_secret)


