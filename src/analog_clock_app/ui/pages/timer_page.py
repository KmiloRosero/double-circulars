from __future__ import annotations

import time
from dataclasses import dataclass

from nicegui import app, ui


@dataclass(slots=True)
class TimerState:
    running: bool
    duration_seconds: float
    start_monotonic: float
    elapsed_seconds: float


def _get_state() -> TimerState:
    data = app.storage.user.get("timer")
    if isinstance(data, dict):
        return TimerState(
            running=bool(data.get("running", False)),
            duration_seconds=float(data.get("duration_seconds", 60.0)),
            start_monotonic=float(data.get("start_monotonic", 0.0)),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
        )
    return TimerState(running=False, duration_seconds=60.0, start_monotonic=0.0, elapsed_seconds=0.0)


def _save_state(state: TimerState) -> None:
    app.storage.user["timer"] = {
        "running": state.running,
        "duration_seconds": state.duration_seconds,
        "start_monotonic": state.start_monotonic,
        "elapsed_seconds": state.elapsed_seconds,
    }


def _elapsed(state: TimerState) -> float:
    if not state.running:
        return state.elapsed_seconds
    return state.elapsed_seconds + (time.monotonic() - state.start_monotonic)


def _remaining(state: TimerState) -> float:
    rem = state.duration_seconds - _elapsed(state)
    return max(0.0, rem)


def _render_timer_svg(remaining_seconds: float, duration_seconds: float) -> str:
    progress = 0.0 if duration_seconds <= 0 else (1.0 - remaining_seconds / duration_seconds)
    progress = min(max(progress, 0.0), 1.0)

    size = 320
    cx = cy = size / 2
    radius = 140

    import math

    angle = (progress * 360.0)
    a = math.radians(angle - 90.0)
    x = cx + radius * 0.85 * math.cos(a)
    y = cy + radius * 0.85 * math.sin(a)

    stroke_len = 2 * math.pi * radius
    dash = stroke_len * progress

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#111827" />'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#374151" stroke-width="14" />'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#10B981" stroke-width="14" '
        f'stroke-dasharray="{dash:.2f} {stroke_len:.2f}" transform="rotate(-90 {cx} {cy})" />'
        f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="#F9FAFB" stroke-width="3" stroke-linecap="round" />'
        f'<circle cx="{cx}" cy="{cy}" r="5" fill="#F9FAFB" />'
        "</svg>"
    )


def timer_page() -> None:
    with ui.column().style("max-width: 1100px; margin: 0 auto; padding: 16px;"):
        ui.label("Temporizador").style("font-weight: 700; font-size: 22px; margin-bottom: 8px;")
        ui.label("Vista analógica (sin reloj digital)").style("opacity: 0.8; margin-top: -6px; margin-bottom: 10px;")

        state = _get_state()

        minutes = ui.number("Minutos", value=int(state.duration_seconds // 60), min=0, max=180, step=1)
        seconds = ui.number("Segundos", value=int(state.duration_seconds % 60), min=0, max=59, step=1)
        ui.separator()

        svg = ui.html(_render_timer_svg(_remaining(state), state.duration_seconds))

        with ui.row().style("gap: 10px;"):
            start_btn = ui.button("Iniciar", color="primary")
            pause_btn = ui.button("Pausar")
            reset_btn = ui.button("Reiniciar", color="negative")

        def on_start() -> None:
            s = _get_state()
            if s.running:
                return
            s.duration_seconds = float(int(minutes.value or 0) * 60 + int(seconds.value or 0))
            if s.duration_seconds <= 0:
                ui.notify("Configura una duración mayor a 0", color="negative")
                return
            s.running = True
            s.start_monotonic = time.monotonic()
            _save_state(s)

        def on_pause() -> None:
            s = _get_state()
            if not s.running:
                return
            s.elapsed_seconds = _elapsed(s)
            s.running = False
            s.start_monotonic = 0.0
            _save_state(s)

        def on_reset() -> None:
            s = _get_state()
            s.running = False
            s.start_monotonic = 0.0
            s.elapsed_seconds = 0.0
            _save_state(s)

        start_btn.on_click(on_start)
        pause_btn.on_click(on_pause)
        reset_btn.on_click(on_reset)

        def tick() -> None:
            s = _get_state()
            rem = _remaining(s)
            svg.content = _render_timer_svg(rem, s.duration_seconds)

            if s.running and rem <= 0.0:
                s.running = False
                s.start_monotonic = 0.0
                s.elapsed_seconds = s.duration_seconds
                _save_state(s)
                ui.notify("¡Temporizador finalizado!", color="warning")

        ui.timer(0.2, tick)

