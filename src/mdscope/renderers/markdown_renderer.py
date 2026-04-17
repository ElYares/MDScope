"""Rich renderers for parsed Markdown documents."""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from mdscope.core.capabilities import TerminalCapabilities
from mdscope.core.markdown_parser import extract_section_text
from mdscope.core.models import ParsedDocument, ProjectDocument
from mdscope.renderers.chart_renderer import ChartAdapter, render_chart_block
from mdscope.renderers.image_renderer import render_image_placeholder
from mdscope.renderers.math_renderer import render_math_block, replace_inline_math
from mdscope.renderers.mermaid_renderer import MermaidAdapter, render_mermaid_block
from mdscope.renderers.table_renderer import render_matrix_block, render_table_block

_SPECIAL_BLOCK_PATTERN = re.compile(
    r"```(?P<kind>mermaid|chart|math|table|matrix)[^\n]*\n(?P<body>.*?)\n```",
    re.DOTALL,
)


def render_markdown_preview(
    document: ProjectDocument,
    parsed: ParsedDocument,
    capabilities: TerminalCapabilities,
    active_anchor: str | None = None,
    mermaid_adapter: MermaidAdapter | None = None,
    chart_adapter: ChartAdapter | None = None,
) -> RenderableType:
    """Build the main preview renderable for an active Markdown document."""
    title = Text(str(document.relative_path), style="bold cyan")
    mode = "documento completo" if active_anchor is None else f"seccion: {active_anchor}"
    subtitle = Text(f"{len(parsed.headings)} headings • {mode}", style="dim")
    body_renderables = _build_body_renderables(
        extract_section_text(parsed, active_anchor),
        capabilities,
        mermaid_adapter=mermaid_adapter,
        chart_adapter=chart_adapter,
    )
    return Group(title, subtitle, Text(""), *body_renderables)


def render_empty_preview(project_root: str) -> RenderableType:
    """Build the preview shown when no Markdown documents exist."""
    return Panel.fit(
        f"No se encontraron archivos Markdown.\n\nRaiz del proyecto: {project_root}",
        title="Preview",
        border_style="yellow",
    )


def _build_body_renderables(
    markdown_text: str,
    capabilities: TerminalCapabilities,
    *,
    mermaid_adapter: MermaidAdapter | None,
    chart_adapter: ChartAdapter | None,
) -> list[RenderableType]:
    renderables: list[RenderableType] = []
    last_end = 0
    for match in _SPECIAL_BLOCK_PATTERN.finditer(markdown_text):
        prefix = markdown_text[last_end : match.start()]
        renderables.extend(_render_markdown_chunk(prefix, capabilities))
        renderables.append(
            _render_special_block(
                match.group("kind"),
                match.group("body"),
                capabilities,
                mermaid_adapter=mermaid_adapter,
                chart_adapter=chart_adapter,
            )
        )
        last_end = match.end()
    suffix = markdown_text[last_end:]
    renderables.extend(_render_markdown_chunk(suffix, capabilities))
    if renderables:
        return renderables
    return [_render_markdown("")]


def _render_markdown_chunk(
    markdown_text: str,
    capabilities: TerminalCapabilities,
) -> list[RenderableType]:
    cleaned = markdown_text.strip()
    if not cleaned:
        return []
    cleaned = _replace_images(cleaned, capabilities)
    cleaned = replace_inline_math(cleaned)
    return [_render_markdown(cleaned)]


def _render_markdown(markdown_text: str) -> Markdown:
    return Markdown(
        markdown_text,
        code_theme="monokai",
        hyperlinks=True,
    )


def _render_special_block(
    kind: str,
    body: str,
    capabilities: TerminalCapabilities,
    *,
    mermaid_adapter: MermaidAdapter | None,
    chart_adapter: ChartAdapter | None,
) -> RenderableType:
    if kind == "mermaid":
        return render_mermaid_block(
            body,
            capabilities,
            adapter=mermaid_adapter,
        )
    if kind == "math":
        return render_math_block(body)
    if kind == "table":
        return render_table_block(body)
    if kind == "matrix":
        return render_matrix_block(body)
    return render_chart_block(body, adapter=chart_adapter)


def _replace_images(markdown_text: str, capabilities: TerminalCapabilities) -> str:
    pattern = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)")

    def replacer(match: re.Match[str]) -> str:
        alt_text = match.group("alt") or None
        image_target = match.group("target")
        panel = render_image_placeholder(image_target, capabilities, alt_text=alt_text)
        return "\n".join(
            [
                f"> [Imagen detectada] {alt_text or Path(image_target).name}",
                f"> Target: {image_target}",
                f"> {panel.title}",
            ]
        )

    return pattern.sub(replacer, markdown_text)
