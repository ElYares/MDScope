"""Fallback rendering for Markdown images."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.panel import Panel
from rich.text import Text

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


def render_image_terminal_art(
    image_path: Path,
    capabilities: TerminalCapabilities,
    *,
    width: int = 72,
    height: int = 24,
) -> Text | None:
    """Render an image to ANSI terminal art when chafa is available."""
    if not capabilities.chafa_available:
        return None
    completed = subprocess.run(
        [
            "chafa",
            "--size",
            f"{width}x{height}",
            str(image_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    return Text.from_ansi(completed.stdout.rstrip())


def _describe_mode(capabilities: TerminalCapabilities) -> str:
    if capabilities.kitty_graphics:
        return "Terminal compatible con Kitty graphics"
    if capabilities.chafa_available:
        return "Fallback potencial con chafa"
    return "Placeholder textual portable"
