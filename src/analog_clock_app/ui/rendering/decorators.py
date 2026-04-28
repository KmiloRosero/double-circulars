from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.clock.models import ClockState

from .interfaces import ClockRenderer


@dataclass(slots=True)
class RendererDecorator(ClockRenderer):
    """Decorator base for renderers.

    Decorators allow layering features (shadow, center dot, theme transforms)
    without changing the base renderer.
    """

    inner: ClockRenderer

    def render(self, state: ClockState, settings: AppSettings) -> str:
        return self.inner.render(state, settings)


class ShadowLayerDecorator(RendererDecorator):
    def render(self, state: ClockState, settings: AppSettings) -> str:
        svg = self.inner.render(state, settings)
        if not settings.enable_shadow_layer:
            return svg
        if "<svg" not in svg:
            return svg
        insert = (
            '<defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
            '<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.35" />'
            "</filter></defs>"
        )
        svg = svg.replace("<svg ", f"<svg filter=\"url(#shadow)\" ", 1)
        return svg.replace(">", f">{insert}", 1)


class CenterDotDecorator(RendererDecorator):
    def render(self, state: ClockState, settings: AppSettings) -> str:
        svg = self.inner.render(state, settings)
        if not settings.enable_center_dot_layer:
            return svg
        if "</svg>" not in svg:
            return svg
        dot = '<circle cx="160" cy="160" r="5" fill="#F9FAFB" />'
        return svg.replace("</svg>", f"{dot}</svg>")

