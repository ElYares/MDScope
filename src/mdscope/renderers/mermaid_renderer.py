"""Renderable helpers for Mermaid blocks."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from rich.console import RenderableType
from rich.panel import Panel

from mdscope.adapters.mermaid_cli import MermaidCliAdapter, MermaidRenderResult
from mdscope.core.capabilities import TerminalCapabilities
from mdscope.renderers.image_renderer import render_image_terminal_art


class MermaidAdapter(Protocol):
    """Protocol for Mermaid render adapters used by the preview renderer."""

    def render_to_png(self, source: str) -> MermaidRenderResult: ...


def render_mermaid_block(
    mermaid_source: str,
    capabilities: TerminalCapabilities,
    *,
    adapter: MermaidAdapter | None = None,
) -> RenderableType:
    """Render a Mermaid block using optional external tooling."""
    active_adapter = adapter or MermaidCliAdapter()
    result = active_adapter.render_to_png(mermaid_source.strip())

    if result.status == "unavailable":
        return Panel.fit(
            "\n".join(
                [
                    "Mermaid detectado.",
                    result.message or "Mermaid CLI no disponible.",
                    "Fallback textual activo.",
                ]
            ),
            title="Mermaid",
            border_style="yellow",
        )

    if result.status == "error" or result.image_path is None:
        message = result.message or "No se pudo renderizar el diagrama Mermaid."
        return Panel.fit(
            "\n".join(
                [
                    "Error al renderizar Mermaid.",
                    message,
                ]
            ),
            title="Mermaid",
            border_style="red",
        )

    return _render_image_result(result.image_path, capabilities, cache_hit=result.cache_hit)


def _render_image_result(
    image_path: Path,
    capabilities: TerminalCapabilities,
    *,
    cache_hit: bool,
) -> RenderableType:
    terminal_art = render_image_terminal_art(image_path, capabilities)
    cache_label = "cache hit" if cache_hit else "cache miss"
    if terminal_art is not None:
        return Panel(
            terminal_art,
            title=f"Mermaid renderizado ({cache_label})",
            border_style="cyan",
        )

    body = "\n".join(
        [
            f"Artefacto generado: {image_path}",
            f"Modo: {_describe_mermaid_mode(capabilities)}",
            f"Estado: {cache_label}",
        ]
    )
    return Panel.fit(body, title="Mermaid renderizado", border_style="cyan")


def _describe_mermaid_mode(capabilities: TerminalCapabilities) -> str:
    if capabilities.chafa_available:
        return "render terminal con chafa"
    if capabilities.kitty_graphics:
        return "artefacto generado; inline Kitty pendiente"
    return "artefacto generado; instala chafa para preview terminal"
