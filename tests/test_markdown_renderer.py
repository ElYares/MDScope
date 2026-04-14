from __future__ import annotations

from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.syntax import Syntax

from mdscope.core.capabilities import TerminalCapabilities
from mdscope.core.markdown_parser import parse_markdown_text
from mdscope.core.models import ProjectDocument
from mdscope.renderers.code_renderer import render_code_block
from mdscope.renderers.markdown_renderer import render_empty_preview, render_markdown_preview


def test_render_code_block_returns_syntax() -> None:
    renderable = render_code_block("print('hola')\n", "python")

    assert isinstance(renderable, Syntax)


def test_render_markdown_preview_returns_group(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(source, "# Titulo\n\nTexto.\n")

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
    )

    assert isinstance(renderable, Group)


def test_render_markdown_preview_accepts_active_anchor(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(source, "# Titulo\n\n## Uso\n\nTexto.\n")

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
        active_anchor="uso",
    )

    assert isinstance(renderable, Group)


def test_render_empty_preview_returns_panel() -> None:
    renderable = render_empty_preview("/tmp/project")

    assert isinstance(renderable, Panel)


def test_render_markdown_preview_replaces_special_fences(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(source, "# Titulo\n\n```mermaid\ngraph TD\nA-->B\n```\n")

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
    )

    assert isinstance(renderable, Group)


def test_render_markdown_preview_replaces_images(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(source, "# Titulo\n\n![Logo](./assets/logo.png)\n")

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=True),
    )

    assert isinstance(renderable, Group)
