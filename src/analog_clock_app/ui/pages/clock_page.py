from __future__ import annotations

from nicegui import ui
from typing import cast

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.config.settings import TimeMode
from analog_clock_app.services.facade import ClockFacade
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.preset_service import PresetService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService
from analog_clock_app.ui.presenter import ClockPresenter


def clock_page(
    facade: ClockFacade,
    settings_service: SettingsService,
    preset_service: PresetService,
    history: HistoryService,
    presenter: ClockPresenter,
) -> None:
    settings = settings_service.get()

    with ui.column().classes("w-full").style("max-width: 1100px; margin: 0 auto; padding: 16px;"):
        with ui.row().classes("w-full").style("gap: 16px; align-items: flex-start;"):
            with ui.card().style("flex: 1; padding: 16px;"):
                ui.label("Reloj").style("font-weight: 700; margin-bottom: 8px;")
                ui.label("Hora local: Pasto, Colombia").style("opacity: 0.8; margin-top: -6px; margin-bottom: 10px;")
                svg_container = ui.html(presenter.render(settings)).classes("w-full")

            with ui.card().style("width: 360px; padding: 16px;"):
                ui.label("Controles").style("font-weight: 700; margin-bottom: 8px;")

                mode = ui.toggle({"real": "Real", "simulated": "Simulado"}, value=settings.time_mode)
                speed = ui.number(
                    "Velocidad de simulación", value=settings.simulation_speed, min=0.1, max=30, step=0.1
                )
                offset = ui.number("Desfase de tiempo (segundos)", value=settings.time_offset_seconds, step=10)

                ui.separator()

                preset_name = ui.input("Nombre de la configuración")
                save_preset_btn = ui.button("Guardar configuración", color="primary")

                presets = preset_service.list_presets()
                preset_options = {p.id: p.name for p in presets}
                preset_select = ui.select(preset_options, label="Configuraciones guardadas")
                apply_preset_btn = ui.button("Aplicar configuración")

                ui.separator()
                undo_btn = ui.button("Deshacer último cambio")
                redo_btn = ui.button("Rehacer")

                ui.separator()
                ui.label("Historial").style("font-weight: 700; margin-bottom: 6px;")
                event_log = ui.column().style("gap: 6px;")

                def render_event_log() -> None:
                    event_log.clear()
                    with event_log:
                        for msg in history.events()[::-1]:
                            ui.label(f"• {msg}").classes("text-sm").style("opacity: 0.85;")

                def refresh_presets() -> None:
                    new_presets = preset_service.list_presets()
                    preset_select.options = {p.id: p.name for p in new_presets}

                def apply_patch(patch: SettingsPatch) -> None:
                    nonlocal settings
                    before = settings
                    settings = settings_service.apply_patch(patch)
                    history.record_change(before, settings, "Se actualizaron los controles")
                    svg_container.content = presenter.render(settings)
                    render_event_log()

                def on_apply_controls() -> None:
                    apply_patch(
                        SettingsPatch(
                            time_mode=cast(TimeMode, mode.value),
                            simulation_speed=float(speed.value or 1.0),
                            time_offset_seconds=int(offset.value or 0),
                        )
                    )

                ui.button("Aplicar", on_click=on_apply_controls, color="primary")

                def on_save_preset() -> None:
                    name = (preset_name.value or "").strip()
                    if not name:
                        ui.notify("Se requiere un nombre", color="negative")
                        return
                    preset_service.save_current_settings_as_preset(name)
                    history.record_change(settings, settings, "Se guardó una configuración")
                    preset_name.value = ""
                    refresh_presets()
                    render_event_log()
                    ui.notify("Configuración guardada", color="positive")

                def on_apply_preset() -> None:
                    nonlocal settings
                    if not preset_select.value:
                        ui.notify("Selecciona una configuración", color="negative")
                        return
                    before = settings
                    settings = preset_service.apply_preset(str(preset_select.value))
                    history.record_change(before, settings, "Se aplicó una configuración")
                    mode.value = settings.time_mode
                    speed.value = settings.simulation_speed
                    offset.value = settings.time_offset_seconds
                    svg_container.content = presenter.render(settings)
                    render_event_log()
                    ui.notify("Configuración aplicada", color="positive")

                def on_undo() -> None:
                    nonlocal settings
                    if not history.can_undo():
                        ui.notify("Nada que deshacer")
                        return
                    settings = history.undo(settings)
                    settings_service.save(settings)
                    mode.value = settings.time_mode
                    speed.value = settings.simulation_speed
                    offset.value = settings.time_offset_seconds
                    svg_container.content = presenter.render(settings)
                    render_event_log()
                    ui.notify("Deshecho", color="positive")

                def on_redo() -> None:
                    nonlocal settings
                    if not history.can_redo():
                        ui.notify("Nada que rehacer")
                        return
                    settings = history.redo(settings)
                    settings_service.save(settings)
                    mode.value = settings.time_mode
                    speed.value = settings.simulation_speed
                    offset.value = settings.time_offset_seconds
                    svg_container.content = presenter.render(settings)
                    render_event_log()
                    ui.notify("Rehecho", color="positive")

                save_preset_btn.on_click(on_save_preset)
                apply_preset_btn.on_click(on_apply_preset)
                undo_btn.on_click(on_undo)
                redo_btn.on_click(on_redo)

                render_event_log()

        def tick() -> None:
            nonlocal settings
            settings = settings_service.get()
            svg_container.content = presenter.render(settings)

        ui.timer(0.2, tick)

