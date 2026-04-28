from __future__ import annotations

import time
from dataclasses import dataclass

from nicegui import app, ui


@dataclass(slots=True)
class StopwatchState:
    running: bool
    start_monotonic: float
    elapsed_seconds: float


def _get_state() -> StopwatchState:
    data = app.storage.user.get("stopwatch")
    if isinstance(data, dict):
        return StopwatchState(
            running=bool(data.get("running", False)),
            start_monotonic=float(data.get("start_monotonic", 0.0)),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
        )
    return StopwatchState(running=False, start_monotonic=0.0, elapsed_seconds=0.0)


def _save_state(state: StopwatchState) -> None:
    app.storage.user["stopwatch"] = {
        "running": state.running,
        "start_monotonic": state.start_monotonic,
        "elapsed_seconds": state.elapsed_seconds,
    }


def _elapsed(state: StopwatchState) -> float:
    if not state.running:
        return state.elapsed_seconds
    return state.elapsed_seconds + (time.monotonic() - state.start_monotonic)


def _render_stopwatch_svg(seconds: float) -> str:
    angle = (seconds % 60.0) / 60.0 * 360.0
    size = 320
    cx = cy = size / 2
    radius = 140

    import math

    a = math.radians(angle - 90.0)
    x = cx + radius * 0.85 * math.cos(a)
    y = cy + radius * 0.85 * math.sin(a)

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#111827" />'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#E5E7EB" stroke-width="3" opacity="0.6" />'
        f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="#F9FAFB" stroke-width="3" stroke-linecap="round" />'
        f'<circle cx="{cx}" cy="{cy}" r="5" fill="#F9FAFB" />'
        "</svg>"
    )


def stopwatch_page() -> None:
    with ui.column().style("max-width: 1100px; margin: 0 auto; padding: 16px;"):
        ui.label("Cronómetro").style("font-weight: 700; font-size: 22px; margin-bottom: 8px;")
        ui.label("Vista analógica (sin reloj digital)").style("opacity: 0.8; margin-top: -6px; margin-bottom: 10px;")

        state = _get_state()
        svg = ui.html(_render_stopwatch_svg(_elapsed(state)))

        with ui.row().style("gap: 10px;"):
            start_btn = ui.button("Iniciar", color="primary")
            pause_btn = ui.button("Pausar")
            reset_btn = ui.button("Reiniciar", color="negative")

        def on_start() -> None:
            s = _get_state()
            if s.running:
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
            _save_state(StopwatchState(running=False, start_monotonic=0.0, elapsed_seconds=0.0))

        start_btn.on_click(on_start)
        pause_btn.on_click(on_pause)
        reset_btn.on_click(on_reset)

        def tick() -> None:
            s = _get_state()
            svg.content = _render_stopwatch_svg(_elapsed(s))

        ui.timer(0.1, tick)

