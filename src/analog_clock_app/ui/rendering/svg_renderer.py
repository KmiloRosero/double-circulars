from __future__ import annotations

from math import cos, radians, sin

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState


class SvgClockRenderer:
    """Base SVG renderer for the analog clock.

    This is intentionally minimal. Visual styling can be extended via decorators.
    """

    def render(self, state: ClockState, settings: AppSettings) -> str:
        size = 320
        cx = cy = size / 2
        radius = 140

        def polar(angle_deg: float, r: float) -> tuple[float, float]:
            a = radians(angle_deg - 90.0)
            return (cx + r * cos(a), cy + r * sin(a))

        tick_lines: list[str] = []
        for tick in state.ticks:
            outer = polar(tick.angle, radius)
            inner_r = radius - (18 if tick.kind == "major" else 10)
            inner = polar(tick.angle, inner_r)
            tick_lines.append(
                f'<line x1="{inner[0]:.2f}" y1="{inner[1]:.2f}" x2="{outer[0]:.2f}" y2="{outer[1]:.2f}" '
                f'stroke="{settings.tick_color}" stroke-width="{3 if tick.kind == "major" else 1.5}" />'
            )

        hour_end = polar(state.angles.hour, radius * 0.55)
        minute_end = polar(state.angles.minute, radius * 0.75)
        second_end = polar(state.angles.second, radius * 0.85)

        hands = "\n".join(
            [
                f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{hour_end[0]:.2f}" y2="{hour_end[1]:.2f}" stroke="{settings.hand_color}" stroke-width="6" stroke-linecap="round" />',
                f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{minute_end[0]:.2f}" y2="{minute_end[1]:.2f}" stroke="{settings.hand_color}" stroke-width="4" stroke-linecap="round" />',
                f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{second_end[0]:.2f}" y2="{second_end[1]:.2f}" stroke="#EF4444" stroke-width="2" stroke-linecap="round" />',
            ]
        )

        svg = (
            f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{settings.face_color}" />'
            + "\n"
            + "\n".join(tick_lines)
            + "\n"
            + hands
            + "</svg>"
        )
        return svg

