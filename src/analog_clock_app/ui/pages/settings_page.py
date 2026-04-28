from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from nicegui import ui

from analog_clock_app.config.settings import BackgroundMode
from analog_clock_app.services.history_service import HistoryService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService
from analog_clock_app.ui.presenter import ClockPresenter


def settings_page(
    settings_service: SettingsService,
    history: HistoryService,
    presenter: ClockPresenter,
    on_settings_changed: Callable[[], None] | None = None,
) -> None:
    settings = settings_service.get()

    with ui.column().style("max-width: 1100px; margin: 0 auto; padding: 16px;"):
        with ui.row().style("gap: 16px; align-items: flex-start;"):
            with ui.card().style("width: 520px; padding: 16px;"):
                ui.label("Configuración").style("font-weight: 700; margin-bottom: 8px;")

                face = ui.input("Color de la esfera (hex)", value=settings.face_color)
                tick = ui.input("Color de marcas (hex)", value=settings.tick_color)
                hand = ui.input("Color de manecillas (hex)", value=settings.hand_color)

                major_only = ui.switch("Solo marcas principales", value=settings.show_major_ticks_only)
                shadow = ui.switch("Capa de sombra", value=settings.enable_shadow_layer)
                center_dot = ui.switch("Punto central", value=settings.enable_center_dot_layer)

                dark_theme = ui.switch("Modo oscuro (negro)", value=settings.dark_theme)

                background_mode = ui.select(
                    {
                        "white": "Fondo blanco",
                        "black": "Fondo negro",
                        "image": "Imagen personalizada",
                    },
                    label="Fondo fuera del recuadro",
                    value=settings.background_mode,
                )

                upload_hint = ui.label("Sube una imagen para usarla como fondo.").style("opacity: 0.8;")
                uploader = ui.upload(label="Subir fondo", auto_upload=True)
                uploader.props("accept=image/*")

                undo_btn = ui.button("Deshacer último cambio")
                redo_btn = ui.button("Rehacer")
                save_btn = ui.button("Guardar", color="primary")

                ui.separator()
                ui.label("Historial").style("font-weight: 700; margin-bottom: 6px;")
                event_log = ui.column().style("gap: 6px;")

            with ui.card().style("flex: 1; padding: 16px;"):
                ui.label("Vista previa").style("font-weight: 700; margin-bottom: 8px;")
                preview = ui.html(presenter.render(settings))

        def apply_patch(patch: SettingsPatch) -> None:
            nonlocal settings
            before = settings
            settings = settings_service.apply_patch(patch)
            history.record_change(before, settings, "Se actualizó la apariencia")
            preview.content = presenter.render(settings)
            render_event_log()
            if on_settings_changed is not None:
                on_settings_changed()

        def refresh_background_controls() -> None:
            mode = cast(BackgroundMode, background_mode.value)
            is_image = mode == "image"
            uploader.set_visibility(is_image)
            upload_hint.set_visibility(is_image)

        async def on_upload(e) -> None:
            content = await e.content.read()
            name = str(getattr(e, "name", "background"))
            ext = Path(name).suffix.lower()
            if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
                ext = ".png"
            filename = f"background{ext}"

            uploads = Path.cwd() / "data" / "uploads"
            uploads.mkdir(parents=True, exist_ok=True)
            (uploads / filename).write_bytes(content)

            apply_patch(SettingsPatch(background_mode="image", background_image_filename=filename))
            ui.notify("Fondo actualizado", color="positive")

        uploader.on_upload(on_upload)
        background_mode.on_value_change(lambda e: refresh_background_controls())
        refresh_background_controls()

        def render_event_log() -> None:
            event_log.clear()
            with event_log:
                for msg in history.events()[::-1]:
                    ui.label(f"• {msg}").classes("text-sm").style("opacity: 0.85;")

        def on_save() -> None:
            apply_patch(
                SettingsPatch(
                    face_color=str(face.value),
                    tick_color=str(tick.value),
                    hand_color=str(hand.value),
                    show_major_ticks_only=bool(major_only.value),
                    enable_shadow_layer=bool(shadow.value),
                    enable_center_dot_layer=bool(center_dot.value),
                    dark_theme=bool(dark_theme.value),
                    background_mode=cast(BackgroundMode, background_mode.value),
                )
            )
            ui.notify("Guardado", color="positive")

        def on_undo() -> None:
            nonlocal settings
            if not history.can_undo():
                ui.notify("Nada que deshacer")
                return
            settings = history.undo(settings)
            settings_service.save(settings)
            face.value = settings.face_color
            tick.value = settings.tick_color
            hand.value = settings.hand_color
            major_only.value = settings.show_major_ticks_only
            shadow.value = settings.enable_shadow_layer
            center_dot.value = settings.enable_center_dot_layer
            dark_theme.value = settings.dark_theme
            background_mode.value = settings.background_mode
            preview.content = presenter.render(settings)
            render_event_log()
            ui.notify("Deshecho", color="positive")
            refresh_background_controls()

        def on_redo() -> None:
            nonlocal settings
            if not history.can_redo():
                ui.notify("Nada que rehacer")
                return
            settings = history.redo(settings)
            settings_service.save(settings)
            face.value = settings.face_color
            tick.value = settings.tick_color
            hand.value = settings.hand_color
            major_only.value = settings.show_major_ticks_only
            shadow.value = settings.enable_shadow_layer
            center_dot.value = settings.enable_center_dot_layer
            dark_theme.value = settings.dark_theme
            background_mode.value = settings.background_mode
            preview.content = presenter.render(settings)
            render_event_log()
            ui.notify("Rehecho", color="positive")
            refresh_background_controls()

        save_btn.on_click(on_save)
        undo_btn.on_click(on_undo)
        redo_btn.on_click(on_redo)

        render_event_log()

