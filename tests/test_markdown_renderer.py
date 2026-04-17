from __future__ import annotations

from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.syntax import Syntax

from mdscope.adapters.mermaid_cli import MermaidRenderResult
from mdscope.adapters.plotext_adapter import ChartRenderResult
from mdscope.core.capabilities import TerminalCapabilities
from mdscope.core.markdown_parser import parse_markdown_text
from mdscope.core.models import ProjectDocument
from mdscope.renderers.code_renderer import render_code_block
from mdscope.renderers.markdown_renderer import render_empty_preview, render_markdown_preview


class FakeMermaidAdapter:
    def render_to_png(self, source: str) -> MermaidRenderResult:
        return MermaidRenderResult(
            status="unavailable",
            message="Mermaid CLI no esta instalado.",
        )


class FakeChartAdapter:
    def render(self, chart_source: str, *, width: int = 72, height: int = 18) -> ChartRenderResult:
        return ChartRenderResult(status="rendered", output="chart")


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
        mermaid_adapter=FakeMermaidAdapter(),
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


def test_render_markdown_preview_renders_chart_blocks(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(
        source,
        "# Titulo\n\n```chart\ntitle: Requests\ny: 1,2,3\n```\n",
    )

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
        chart_adapter=FakeChartAdapter(),
    )

    assert isinstance(renderable, Group)


def test_render_markdown_preview_renders_math_blocks(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(
        source,
        "# Titulo\n\n```math\nREE = 10 \\times peso_{kg} + 6.25 \\times talla_{cm}\n```\n",
    )

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
    )

    assert isinstance(renderable, Group)


def test_render_markdown_preview_renders_table_blocks(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(
        source,
        "# Titulo\n\n```table\nMetodo|Formula|Inputs\nMifflin|10xkg|peso,talla\n```\n",
    )

    renderable = render_markdown_preview(
        document,
        parsed,
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
    )

    assert isinstance(renderable, Group)


def test_render_markdown_preview_renders_matrix_blocks(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    document = ProjectDocument(path=source, relative_path=Path("README.md"))
    parsed = parse_markdown_text(
        source,
        "# Titulo\n\n```matrix\n1,2,3\n4,5,6\n```\n",
    )

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
