"""Renderable helpers for chart blocks."""

from __future__ import annotations

from typing import Protocol

from rich.panel import Panel
from rich.text import Text

from mdscope.adapters.plotext_adapter import ChartRenderResult, PlotextAdapter


class ChartAdapter(Protocol):
    """Protocol for chart render adapters used by the preview renderer."""

    def render(
        self,
        chart_source: str,
        *,
        width: int = 72,
        height: int = 18,
    ) -> ChartRenderResult: ...


def render_chart_block(
    chart_source: str,
    *,
    adapter: ChartAdapter | None = None,
) -> Panel:
    """Render a chart block using plotext when available."""
    active_adapter = adapter or PlotextAdapter()
    result = active_adapter.render(chart_source)

    if result.status == "rendered" and result.output is not None:
        return Panel(
            Text.from_ansi(result.output),
            title="Chart renderizado",
            border_style="green",
        )

    if result.status == "invalid":
        body = "\n".join(
            [
                "Bloque chart invalido.",
                result.message or "No se pudo interpretar el bloque.",
            ]
        )
        return Panel.fit(body, title="Chart", border_style="red")

    if result.status == "unavailable":
        body = "\n".join(
            [
                "Chart detectado.",
                result.message or "plotext no disponible.",
                "Fallback textual activo.",
            ]
        )
        return Panel.fit(body, title="Chart", border_style="yellow")

    body = "\n".join(
        [
            "Error al renderizar chart.",
            result.message or "plotext fallo.",
        ]
    )
    return Panel.fit(body, title="Chart", border_style="red")
