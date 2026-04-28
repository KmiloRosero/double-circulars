from __future__ import annotations

from datetime import datetime, timezone

from nicegui import ui

from analog_clock_app.services.alarm_service import AlarmService
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.settings_service import SettingsService


def alarms_page(settings_service: SettingsService, alarm_service: AlarmService, history: HistoryService) -> None:
    settings = settings_service.get()

    with ui.column().style("max-width: 1100px; margin: 0 auto; padding: 16px;"):
        ui.label("Alarmas").style("font-weight: 700; font-size: 22px; margin-bottom: 8px;")

        with ui.card().style("padding: 16px;"):
            ui.label("Crear alarma").style("font-weight: 700; margin-bottom: 8px;")

            label = ui.input("Etiqueta", placeholder="Ej: Clase, Despertar")

            hour = ui.select({str(h): f"{h:02d}" for h in range(24)}, label="Hora", value="7")
            minute = ui.select({str(m): f"{m:02d}" for m in range(0, 60, 5)}, label="Minuto", value="0")

            ui.label("Zona horaria usada: Pasto/Colombia (America/Bogota)").style("opacity: 0.8;")

            def on_create() -> None:
                name = (label.value or "").strip() or "Alarma"
                alarm_service.add_alarm(
                    label=name,
                    hour=int(hour.value),
                    minute=int(minute.value),
                    timezone=settings.timezone,
                )
                history.record_change(settings, settings, "Se creó una alarma")
                label.value = ""
                refresh_list()
                ui.notify("Alarma creada", color="positive")

            ui.button("Crear", on_click=on_create, color="primary")

        ui.separator()

        ui.label("Mis alarmas").style("font-weight: 700; margin-bottom: 6px;")

        alarms_container = ui.column().style("gap: 10px;")

        def refresh_list() -> None:
            alarms_container.clear()
            alarms = alarm_service.list_alarms()

            with alarms_container:
                if not alarms:
                    ui.label("No hay alarmas creadas.").style("opacity: 0.8;")
                    return

                for alarm in alarms:
                    with ui.card().style("padding: 12px;"):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"{alarm.label} — {alarm.hour:02d}:{alarm.minute:02d}").style(
                                "font-weight: 600;"
                            )
                            enabled = ui.switch("Activa", value=alarm.enabled)

                        with ui.row().style("gap: 10px;"):
                            def on_delete(a_id: str = alarm.id) -> None:
                                alarm_service.delete_alarm(a_id)
                                history.record_change(settings, settings, "Se eliminó una alarma")
                                refresh_list()

                            ui.button("Eliminar", on_click=on_delete, color="negative")

                        def on_toggle(value: bool, a_id: str = alarm.id) -> None:
                            alarm_service.set_enabled(a_id, bool(value))
                            history.record_change(settings, settings, "Se cambió el estado de una alarma")

                        enabled.on_value_change(lambda e, a_id=alarm.id: on_toggle(bool(e.value), a_id))

        refresh_list()

        def poll_alarms() -> None:
            now_utc = datetime.now(timezone.utc)
            due = alarm_service.check_due(now_utc)
            if not due:
                return

            for alarm in due:
                ui.notify(f"Alarma: {alarm.label}", color="warning")

                with ui.dialog().props("persistent") as dialog:
                    with ui.card().style("padding: 16px; min-width: 320px;"):
                        ui.label("¡Alarma!").style("font-weight: 800; font-size: 20px;")
                        ui.label(alarm.label).style("margin-top: 6px;")
                        ui.button("Aceptar", on_click=dialog.close, color="primary")
                dialog.open()

        ui.timer(1.0, poll_alarms)
