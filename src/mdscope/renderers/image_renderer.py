"""Rendering helpers for Markdown images."""

from __future__ import annotations

import base64
import hashlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from mdscope.core.capabilities import TerminalCapabilities

_KITTY_PLACEHOLDER = chr(0x10EEEE)
_KITTY_DOC_ROOT = Path("/usr/share/doc/kitty")
_KITTY_SENT_IMAGES: set[tuple[str, int, int, int]] = set()


def render_markdown_image(
    image_target: str,
    source_path: Path,
    capabilities: TerminalCapabilities,
    *,
    alt_text: str | None = None,
) -> RenderableType:
    """Render a Markdown image using the best available terminal strategy."""
    title = alt_text or Path(image_target).name or "Imagen Markdown"
    resolved_path = resolve_image_path(image_target, source_path)

    if resolved_path is None:
        return render_image_placeholder(
            image_target,
            capabilities,
            alt_text=title,
            detail="Ruta remota o no soportada para preview inline.",
        )

    if not resolved_path.exists():
        return render_image_placeholder(
            image_target,
            capabilities,
            alt_text=title,
            resolved_path=resolved_path,
            detail="Archivo no encontrado desde la ruta del documento.",
        )

    terminal_art = render_image_terminal_art(resolved_path, capabilities)
    if terminal_art is not None:
        return Panel(terminal_art, title=title, border_style="cyan")

    return render_image_placeholder(
        image_target,
        capabilities,
        alt_text=title,
        resolved_path=resolved_path,
        detail="Preview inline no disponible en este terminal.",
    )


def render_image_placeholder(
    image_target: str,
    capabilities: TerminalCapabilities,
    *,
    alt_text: str | None = None,
    resolved_path: Path | None = None,
    detail: str | None = None,
) -> Panel:
    """Render a capability-aware placeholder for an image."""
    mode = _describe_mode(capabilities)
    title = alt_text or "Imagen Markdown"
    body_lines = [
        f"Target: {image_target}",
        f"Nombre: {Path(image_target).name}",
    ]
    if resolved_path is not None:
        body_lines.append(f"Resuelta: {resolved_path}")
    body_lines.append("Presiona `o` para abrir la imagen real.")
    body_lines.append(f"Modo: {mode}")
    if detail is not None:
        body_lines.append(f"Estado: {detail}")
    body = "\n".join(body_lines)
    return Panel.fit(body, title=title, border_style="cyan")


def render_image_terminal_art(
    image_path: Path,
    capabilities: TerminalCapabilities,
    *,
    width: int = 72,
    height: int = 24,
) -> Text | None:
    """Render an image using the best terminal-specific preview available."""
    kitty_renderable = render_image_kitty_art(
        image_path,
        capabilities,
        width=width,
        height=height,
    )
    if kitty_renderable is not None:
        return kitty_renderable
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


def render_image_kitty_art(
    image_path: Path,
    capabilities: TerminalCapabilities,
    *,
    width: int = 72,
    height: int = 24,
) -> Text | None:
    """Render an image using Kitty Unicode placeholders when supported."""
    if not capabilities.kitty_graphics:
        return None

    cols = max(1, width)
    rows = max(1, height)
    image_id = _kitty_image_id(image_path, cols, rows)
    if not _ensure_kitty_virtual_placement(image_path, image_id=image_id, cols=cols, rows=rows):
        return None

    style = Style(color=f"#{image_id:06x}")
    placeholder = Text(style=style)
    for row in range(rows):
        prefix = _KITTY_PLACEHOLDER + _kitty_row_diacritic(row)
        placeholder.append(prefix, style=style)
        if cols > 1:
            placeholder.append(_KITTY_PLACEHOLDER * (cols - 1), style=style)
        if row < rows - 1:
            placeholder.append("\n")
    return placeholder


def _describe_mode(capabilities: TerminalCapabilities) -> str:
    if capabilities.kitty_graphics:
        return "Render nativo con Kitty graphics"
    if capabilities.chafa_available:
        return "Render ANSI con chafa"
    return "Placeholder textual portable"


def resolve_image_path(image_target: str, source_path: Path) -> Path | None:
    """Resolve a Markdown image target relative to the source document."""
    lowered = image_target.lower()
    if lowered.startswith(("http://", "https://", "data:")):
        return None
    target_path = Path(image_target)
    if target_path.is_absolute():
        return target_path
    return source_path.parent / target_path


def _kitty_image_id(image_path: Path, cols: int, rows: int) -> int:
    digest = hashlib.sha256(f"{image_path.resolve()}:{cols}:{rows}".encode("utf-8")).digest()
    image_id = int.from_bytes(digest[:3], "big")
    return max(1, image_id)


def _ensure_kitty_virtual_placement(
    image_path: Path,
    *,
    image_id: int,
    cols: int,
    rows: int,
) -> bool:
    try:
        mtime_ns = image_path.stat().st_mtime_ns
    except OSError:
        return False
    cache_key = (str(image_path.resolve()), cols, rows, mtime_ns)
    if cache_key in _KITTY_SENT_IMAGES:
        return True
    command = _serialize_kitty_virtual_placement(
        image_path,
        image_id=image_id,
        cols=cols,
        rows=rows,
    )
    try:
        with open("/dev/tty", "wb", buffering=0) as terminal:
            terminal.write(command)
    except OSError:
        return False
    _KITTY_SENT_IMAGES.add(cache_key)
    return True


def _serialize_kitty_virtual_placement(
    image_path: Path,
    *,
    image_id: int,
    cols: int,
    rows: int,
) -> bytes:
    control = {
        "a": "T",
        "q": 2,
        "f": 100,
        "t": "f",
        "U": 1,
        "i": image_id,
        "c": cols,
        "r": rows,
    }
    payload = base64.standard_b64encode(os.fsencode(image_path))
    command = ",".join(f"{key}={value}" for key, value in control.items()).encode("ascii")
    return b"\033_G" + command + b";" + payload + b"\033\\"


@lru_cache(maxsize=1)
def _kitty_row_diacritics() -> tuple[str, ...]:
    search_roots = (
        _KITTY_DOC_ROOT,
        Path("/usr/share/doc"),
    )
    for root in search_roots:
        if not root.exists():
            continue
        matches = sorted(root.rglob("rowcolumn-diacritics.txt"))
        if not matches:
            continue
        diacritics: list[str] = []
        for line in matches[0].read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.startswith("#"):
                continue
            codepoint = line.split(";", maxsplit=1)[0]
            diacritics.append(chr(int(codepoint, 16)))
        if diacritics:
            return tuple(diacritics)
    return (
        "\u0305",
        "\u030d",
        "\u030e",
        "\u0310",
        "\u0312",
        "\u033d",
        "\u033e",
        "\u033f",
        "\u0346",
        "\u034a",
        "\u034b",
        "\u034c",
        "\u0350",
        "\u0351",
        "\u0352",
        "\u0357",
        "\u035b",
        "\u0363",
        "\u0364",
        "\u0365",
        "\u0366",
        "\u0367",
        "\u0368",
        "\u0369",
        "\u036a",
        "\u036b",
        "\u036c",
        "\u036d",
        "\u036e",
        "\u036f",
        "\u0483",
        "\u0484",
        "\u0485",
        "\u0486",
        "\u0487",
        "\u0592",
        "\u0593",
        "\u0594",
        "\u0595",
        "\u0597",
    )


def _kitty_row_diacritic(row: int) -> str:
    diacritics = _kitty_row_diacritics()
    if row >= len(diacritics):
        return diacritics[-1]
    return diacritics[row]
