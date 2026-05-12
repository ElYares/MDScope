from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from mdscope.core.capabilities import TerminalCapabilities
from mdscope.renderers.image_renderer import (
    _KITTY_PLACEHOLDER,
    _serialize_kitty_virtual_placement,
    render_image_kitty_art,
    render_markdown_image,
    render_image_terminal_art,
    resolve_image_path,
)


def test_resolve_image_path_uses_document_directory(tmp_path: Path) -> None:
    source = tmp_path / "docs" / "guide.md"
    source.parent.mkdir()
    resolved = resolve_image_path("./assets/logo.png", source)

    assert resolved == source.parent / "assets" / "logo.png"


def test_render_markdown_image_returns_missing_file_placeholder(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    renderable = render_markdown_image(
        "./assets/logo.png",
        source,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
        alt_text="Logo",
    )

    assert isinstance(renderable, Panel)
    assert "Archivo no encontrado" in str(renderable.renderable)
    assert "Presiona `o` para abrir la imagen real." in str(renderable.renderable)


def test_render_markdown_image_returns_terminal_art_panel(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "guide.md"
    image_path = tmp_path / "assets" / "logo.png"
    image_path.parent.mkdir()
    image_path.write_bytes(b"png")

    monkeypatch.setattr(
        "mdscope.renderers.image_renderer.render_image_terminal_art",
        lambda *_args, **_kwargs: Text("ANSI ART"),
    )

    renderable = render_markdown_image(
        "./assets/logo.png",
        source,
        TerminalCapabilities(kitty_graphics=False, chafa_available=True),
        alt_text="Logo",
    )

    assert isinstance(renderable, Panel)
    assert str(renderable.renderable) == "ANSI ART"


def test_render_image_kitty_art_returns_unicode_placeholder(
    tmp_path: Path,
    monkeypatch,
) -> None:
    image_path = tmp_path / "diagram.png"
    image_path.write_bytes(b"png")

    monkeypatch.setattr(
        "mdscope.renderers.image_renderer._ensure_kitty_virtual_placement",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        "mdscope.renderers.image_renderer._kitty_row_diacritics",
        lambda: ("\u0305", "\u030d"),
    )

    renderable = render_image_kitty_art(
        image_path,
        TerminalCapabilities(kitty_graphics=True, chafa_available=False),
        width=3,
        height=2,
    )

    assert isinstance(renderable, Text)
    assert renderable.plain.count(_KITTY_PLACEHOLDER) == 6
    assert "\n" in renderable.plain


def test_render_image_terminal_art_prefers_kitty_over_chafa(
    tmp_path: Path,
    monkeypatch,
) -> None:
    image_path = tmp_path / "diagram.png"
    image_path.write_bytes(b"png")

    monkeypatch.setattr(
        "mdscope.renderers.image_renderer.render_image_kitty_art",
        lambda *_args, **_kwargs: Text("KITTY"),
    )

    renderable = render_image_terminal_art(
        image_path,
        TerminalCapabilities(kitty_graphics=True, chafa_available=True),
    )

    assert isinstance(renderable, Text)
    assert renderable.plain == "KITTY"


def test_serialize_kitty_virtual_placement_uses_combined_transmit_and_placeholder(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "diagram.png"
    image_path.write_bytes(b"png")

    command = _serialize_kitty_virtual_placement(
        image_path,
        image_id=42,
        cols=10,
        rows=4,
    )

    assert b"a=T" in command
    assert b"U=1" in command
    assert b"i=42" in command
    assert b"c=10" in command
    assert b"r=4" in command
