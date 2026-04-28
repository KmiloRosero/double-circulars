from __future__ import annotations

from nicegui import ui


def about_page() -> None:
    with ui.column().style("max-width: 900px; margin: 0 auto; padding: 16px;"):
        ui.label("Acerca de").style("font-weight: 700; font-size: 22px; margin-bottom: 8px;")

        ui.markdown(
            """
Este proyecto renderiza un reloj analógico en el navegador usando una arquitectura 100% Python.

Idea principal:
- Una lista doblemente enlazada circular de 60 nodos representa las marcas del reloj.
- El motor recorre ese anillo para generar las marcas y calcula los ángulos de las manecillas.

Persistencia:
- La configuración y las configuraciones guardadas se almacenan en SQLite.
"""
        )

