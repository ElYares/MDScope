from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.panel import Panel

from mdscope.adapters.mermaid_cli import MermaidRenderResult
from mdscope.core.capabilities import TerminalCapabilities
from mdscope.renderers.mermaid_renderer import render_mermaid_block


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

    assert isinstance(renderable, Panel)
