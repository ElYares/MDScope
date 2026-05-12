from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Group
from rich.panel import Panel

from mdscope.adapters.mermaid_cli import MermaidRenderResult
from mdscope.core.capabilities import TerminalCapabilities
from mdscope.renderers.mermaid_renderer import (
    _build_textual_summary,
    render_mermaid_block,
)


@dataclass
class FakeMermaidAdapter:
    result: MermaidRenderResult

    def render_to_png(self, source: str) -> MermaidRenderResult:
        return self.result


def test_render_mermaid_block_returns_unavailable_panel(tmp_path: Path) -> None:
    adapter = FakeMermaidAdapter(
        MermaidRenderResult(status="unavailable", message="Mermaid CLI no esta instalado.")
    )

    renderable = render_mermaid_block(
        "graph TD\nA-->B\n",
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
        adapter=adapter,
    )

    assert isinstance(renderable, Panel)


def test_render_mermaid_block_returns_generated_panel_without_image_terminal_support(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "diagram.png"
    image_path.write_bytes(b"png")
    adapter = FakeMermaidAdapter(MermaidRenderResult(status="rendered", image_path=image_path))

    renderable = render_mermaid_block(
        "graph TD\nA-->B\n",
        TerminalCapabilities(kitty_graphics=False, chafa_available=False),
        adapter=adapter,
    )

    assert isinstance(renderable, Group)
    assert "Presiona `o` para abrir la imagen real." in str(renderable.renderables[0].renderable)


def test_build_textual_summary_for_flowchart_extracts_edges() -> None:
    summary = _build_textual_summary(
        "flowchart LR\nA[CSV ventas POS] --> B[Airbyte o carga Python]\nB --> C[Landing raw]\n"
    )

    assert "Flowchart LR" in summary
    assert "CSV ventas POS -> Airbyte o carga Python" in summary
    assert "Airbyte o carga Python -> Landing raw" in summary


def test_build_textual_summary_for_pie_extracts_segments() -> None:
    summary = _build_textual_summary(
        'pie title Distribucion\n"Droplet" : 417.72\n"Spaces" : 87.03\n'
    )

    assert "Pie title Distribucion" in summary
    assert "- Droplet: 417.72" in summary
    assert "- Spaces: 87.03" in summary
