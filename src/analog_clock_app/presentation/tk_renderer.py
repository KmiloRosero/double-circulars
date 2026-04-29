from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Protocol

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState


class CanvasLike(Protocol):
    def delete(self, tag: str) -> None: ...

    def configure(self, **kwargs) -> None: ...

    def create_oval(self, *args, **kwargs) -> int: ...

    def create_line(self, *args, **kwargs) -> int: ...

    def create_arc(self, *args, **kwargs) -> int: ...


class ClockCanvasRenderer(Protocol):
    def render(self, canvas: CanvasLike, state: ClockState, settings: AppSettings, size: int) -> None: ...


class TkBaseClockRenderer:
    def render(self, canvas: CanvasLike, state: ClockState, settings: AppSettings, size: int) -> None:
        canvas.delete("all")
        s = float(size)
        cx = cy = s / 2
        radius = min(s, s) * 0.44

        face = settings.face_color
        tick = settings.tick_color
        hand = settings.hand_color

        canvas.configure(bg=face)
        canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline=tick,
            width=3,
        )

        def polar(angle_deg: float, r: float) -> tuple[float, float]:
            a = radians(angle_deg - 90.0)
            return cx + r * cos(a), cy + r * sin(a)

        for t in state.ticks:
            outer = polar(t.angle, radius)
            inner = polar(t.angle, radius - (18 if t.kind == "major" else 10))
            width = 3 if t.kind == "major" else 1
            canvas.create_line(inner[0], inner[1], outer[0], outer[1], fill=tick, width=width)

        hour_end = polar(state.angles.hour, radius * 0.55)
        minute_end = polar(state.angles.minute, radius * 0.75)
        second_end = polar(state.angles.second, radius * 0.85)

        canvas.create_line(cx, cy, hour_end[0], hour_end[1], fill=hand, width=6)
        canvas.create_line(cx, cy, minute_end[0], minute_end[1], fill=hand, width=4)
        canvas.create_line(cx, cy, second_end[0], second_end[1], fill="#EF4444", width=2)


@dataclass(slots=True)
class RendererDecorator(ClockCanvasRenderer):
    inner: ClockCanvasRenderer

    def render(self, canvas: CanvasLike, state: ClockState, settings: AppSettings, size: int) -> None:
        self.inner.render(canvas, state, settings, size)


class ShadowLayerDecorator(RendererDecorator):
    def render(self, canvas: CanvasLike, state: ClockState, settings: AppSettings, size: int) -> None:
        self.inner.render(canvas, state, settings, size)
        if not settings.enable_shadow_layer:
            return

        s = float(size)
        cx = cy = s / 2
        radius = min(s, s) * 0.44

        def polar(angle_deg: float, r: float) -> tuple[float, float]:
            a = radians(angle_deg - 90.0)
            return cx + r * cos(a), cy + r * sin(a)

        off = 2
        hour_end = polar(state.angles.hour, radius * 0.55)
        minute_end = polar(state.angles.minute, radius * 0.75)
        canvas.create_line(cx + off, cy + off, hour_end[0] + off, hour_end[1] + off, fill="#000000", width=6)
        canvas.create_line(
            cx + off, cy + off, minute_end[0] + off, minute_end[1] + off, fill="#000000", width=4
        )


class CenterDotDecorator(RendererDecorator):
    def render(self, canvas: CanvasLike, state: ClockState, settings: AppSettings, size: int) -> None:
        self.inner.render(canvas, state, settings, size)
        if not settings.enable_center_dot_layer:
            return
        s = float(size)
        cx = cy = s / 2
        hand = settings.hand_color
        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=hand, outline=hand)

