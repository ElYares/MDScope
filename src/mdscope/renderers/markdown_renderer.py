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
from mdscope.renderers.image_renderer import render_image_placeholder


def render_markdown_preview(
    document: ProjectDocument,
    parsed: ParsedDocument,
    capabilities: TerminalCapabilities,
    active_anchor: str | None = None,
) -> RenderableType:
    """Build the main preview renderable for an active Markdown document."""
    title = Text(str(document.relative_path), style="bold cyan")
    mode = "documento completo" if active_anchor is None else f"seccion: {active_anchor}"
    subtitle = Text(f"{len(parsed.headings)} headings • {mode}", style="dim")
    markdown_source = _replace_special_content(
        extract_section_text(parsed, active_anchor),
        capabilities,
    )
    markdown = Markdown(
        markdown_source,
        code_theme="monokai",
        hyperlinks=True,
    )
    return Group(title, subtitle, Text(""), markdown)


def render_empty_preview(project_root: str) -> RenderableType:
    """Build the preview shown when no Markdown documents exist."""
    return Panel.fit(
        f"No se encontraron archivos Markdown.\n\nRaiz del proyecto: {project_root}",
        title="Preview",
        border_style="yellow",
    )


def _replace_special_content(
    markdown_text: str,
    capabilities: TerminalCapabilities,
) -> str:
    markdown_text = _replace_special_fence(markdown_text, "mermaid", "Mermaid detectado")
    markdown_text = _replace_special_fence(markdown_text, "chart", "Chart detectado")
    markdown_text = _replace_images(markdown_text, capabilities)
    return markdown_text


def _replace_special_fence(markdown_text: str, fence_name: str, label: str) -> str:
    pattern = re.compile(
        rf"```{re.escape(fence_name)}[^\n]*\n(.*?)\n```",
        re.DOTALL,
    )

    def replacer(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        line_count = 0 if not body else len(body.splitlines())
        return "\n".join(
            [
                f"> [{label}]",
                "> Render enriquecido no disponible en este MVP.",
                f"> Bloque con {line_count} lineas.",
            ]
        )

    return pattern.sub(replacer, markdown_text)


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
