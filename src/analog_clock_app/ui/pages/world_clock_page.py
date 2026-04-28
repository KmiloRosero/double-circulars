from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from nicegui import ui

from analog_clock_app.domain.clock.engine import ClockEngine
from analog_clock_app.services.clock_service import ClockService
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.settings_service import SettingsService
from analog_clock_app.services.world_clock_service import WorldClockService
from analog_clock_app.ui.rendering.interfaces import ClockRenderer


def world_clock_page(
    settings_service: SettingsService,
    world_clock_service: WorldClockService,
    history: HistoryService,
    renderer: ClockRenderer,
) -> None:
    settings = settings_service.get()
    engine = ClockEngine()

    cities: dict[str, str] = {
        "Pasto, Colombia": "America/Bogota",
        "New York, USA": "America/New_York",
        "Mexico City, Mexico": "America/Mexico_City",
        "Buenos Aires, Argentina": "America/Argentina/Buenos_Aires",
        "London, UK": "Europe/London",
        "Madrid, España": "Europe/Madrid",
        "Tokyo, Japón": "Asia/Tokyo",
        "Sydney, Australia": "Australia/Sydney",
    }

    with ui.column().style("max-width: 1100px; margin: 0 auto; padding: 16px;"):
        ui.label("Reloj mundial").style("font-weight: 700; font-size: 22px; margin-bottom: 8px;")

        with ui.card().style("padding: 16px;"):
            ui.label("Agregar ciudad").style("font-weight: 700; margin-bottom: 8px;")
            city_label = ui.select(list(cities.keys()), label="Ciudad")

            def on_add() -> None:
                if not city_label.value:
                    ui.notify("Selecciona una ciudad", color="negative")
                    return
                label = str(city_label.value)
                tz_name = cities[label]
                world_clock_service.add_favorite(label=label, timezone=tz_name)
                history.record_change(settings, settings, "Se agregó una ciudad al reloj mundial")
                refresh()

            ui.button("Agregar", on_click=on_add, color="primary")

        ui.separator()

        clocks = ui.row().style("gap: 12px; flex-wrap: wrap;")

        def render_city_svg(tz_name: str) -> str:
            now_utc = datetime.now(timezone.utc)
            local = ClockService._to_local_time(now_utc, tz_name)
            state = engine.state_from_datetime(local, major_ticks_only=settings.show_major_ticks_only)
            return renderer.render(state, settings)

        def refresh() -> None:
            clocks.clear()
            favorites = world_clock_service.list_favorites()
            with clocks:
                if not favorites:
                    ui.label("Aún no has agregado ciudades.").style("opacity: 0.8;")
                    return
                for fav in favorites:
                    with ui.card().style("padding: 12px; width: 260px;"):
                        ui.label(fav.label).style("font-weight: 700; margin-bottom: 6px;")
                        svg = ui.html(render_city_svg(fav.timezone))
                        def on_remove(fid: str = fav.id) -> None:
                            world_clock_service.delete_favorite(fid)
                            history.record_change(settings, settings, "Se quitó una ciudad del reloj mundial")
                            refresh()

                        ui.button("Quitar", on_click=on_remove, color="negative")

                        def tick(tz_name: str = fav.timezone, svg_el=svg) -> None:
                            svg_el.content = render_city_svg(tz_name)

                        ui.timer(1.0, tick)

        refresh()
