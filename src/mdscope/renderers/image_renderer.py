"""Fallback rendering for Markdown images."""

from __future__ import annotations

from pathlib import Path

from rich.panel import Panel

from mdscope.core.capabilities import TerminalCapabilities


def render_image_placeholder(
    image_target: str,
    capabilities: TerminalCapabilities,
    *,
    alt_text: str | None = None,
) -> Panel:
    """Render a capability-aware placeholder for an image."""
    mode = _describe_mode(capabilities)
    title = alt_text or "Imagen Markdown"
    body = "\n".join(
        [
            f"Target: {image_target}",
            f"Nombre: {Path(image_target).name}",
            f"Modo: {mode}",
        ]
    )
    return Panel.fit(body, title=title, border_style="cyan")


def _describe_mode(capabilities: TerminalCapabilities) -> str:
    if capabilities.kitty_graphics:
        return "Terminal compatible con Kitty graphics"
    if capabilities.chafa_available:
        return "Fallback potencial con chafa"
    return "Placeholder textual portable"
