"""Renderable helpers for Mermaid blocks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from mdscope.adapters.mermaid_cli import MermaidCliAdapter, MermaidRenderResult
from mdscope.core.capabilities import TerminalCapabilities
from mdscope.renderers.image_renderer import render_image_terminal_art


class MermaidAdapter(Protocol):
    """Protocol for Mermaid render adapters used by the preview renderer."""

    def render_to_png(self, source: str) -> MermaidRenderResult: ...


def render_mermaid_block(
    mermaid_source: str,
    capabilities: TerminalCapabilities,
    *,
    adapter: MermaidAdapter | None = None,
) -> RenderableType:
    """Render a Mermaid block using optional external tooling."""
    active_adapter = adapter or MermaidCliAdapter()
    result = active_adapter.render_to_png(mermaid_source.strip())

    if result.status == "unavailable":
        return Panel.fit(
            "\n".join(
                [
                    "Mermaid detectado.",
                    result.message or "Mermaid CLI no disponible.",
                    "Fallback textual activo.",
                ]
            ),
            title="Mermaid",
            border_style="yellow",
        )

    if result.status == "error" or result.image_path is None:
        message = result.message or "No se pudo renderizar el diagrama Mermaid."
        return Panel.fit(
            "\n".join(
                [
                    "Error al renderizar Mermaid.",
                    message,
                ]
            ),
            title="Mermaid",
            border_style="red",
        )

    return _render_image_result(
        result.image_path,
        mermaid_source,
        capabilities,
        cache_hit=result.cache_hit,
    )


def _render_image_result(
    image_path: Path,
    mermaid_source: str,
    capabilities: TerminalCapabilities,
    *,
    cache_hit: bool,
) -> RenderableType:
    cache_label = "cache hit" if cache_hit else "cache miss"
    if capabilities.kitty_graphics:
        terminal_art = render_image_terminal_art(image_path, capabilities)
        if terminal_art is not None:
            return Panel(
                terminal_art,
                title=f"Mermaid renderizado ({cache_label})",
                border_style="cyan",
            )

    return _render_textual_fallback(
        mermaid_source,
        image_path,
        capabilities,
        cache_label=cache_label,
    )


def _render_textual_fallback(
    mermaid_source: str,
    image_path: Path,
    capabilities: TerminalCapabilities,
    *,
    cache_label: str,
) -> RenderableType:
    summary = _build_textual_summary(mermaid_source)
    body = Panel.fit(
        "\n".join(
            [
                summary,
                "",
                "Presiona `o` para abrir la imagen real.",
                f"Artefacto: {image_path.name}",
                f"Modo: {_describe_mermaid_mode(capabilities)}",
                f"Estado: {cache_label}",
            ]
        ),
        title="Mermaid",
        border_style="cyan",
    )
    source = Syntax(mermaid_source.strip(), "text", theme="monokai", word_wrap=True)
    return Group(body, Text(""), Text("Fuente Mermaid", style="bold magenta"), source)


def _describe_mermaid_mode(capabilities: TerminalCapabilities) -> str:
    if capabilities.kitty_graphics:
        return "render nativo con Kitty graphics"
    if capabilities.chafa_available:
        return "resumen textual legible"
    return "fallback textual portable"


def _build_textual_summary(mermaid_source: str) -> str:
    lines = [line.strip() for line in mermaid_source.splitlines() if line.strip()]
    if not lines:
        return "Diagrama Mermaid vacio."
    header = lines[0].lower()
    if header.startswith("flowchart"):
        return _summarize_flowchart(lines)
    if header.startswith("pie"):
        return _summarize_pie(lines)
    return "Preview textual de Mermaid."


def _summarize_flowchart(lines: list[str]) -> str:
    direction = lines[0].split(maxsplit=1)[1] if len(lines[0].split()) > 1 else "TD"
    edges: list[str] = []
    node_labels: dict[str, str] = {}
    for raw_line in lines[1:]:
        cleaned = raw_line.strip()
        if not cleaned or cleaned.startswith("%"):
            continue
        if cleaned.startswith("subgraph") or cleaned == "end":
            continue
        if "-->" not in cleaned:
            continue
        edge = _parse_flowchart_edge(cleaned, node_labels)
        if edge is not None:
            edges.append(edge)
    if not edges:
        return f"Flowchart {direction}\nNo se pudieron extraer relaciones legibles."
    limited_edges = edges[:10]
    summary_lines = [f"Flowchart {direction}", *[f"{index + 1}. {edge}" for index, edge in enumerate(limited_edges)]]
    if len(edges) > len(limited_edges):
        summary_lines.append(f"... y {len(edges) - len(limited_edges)} relaciones mas.")
    return "\n".join(summary_lines)


def _parse_flowchart_edge(line: str, node_labels: dict[str, str]) -> str | None:
    match = re.match(r"(?P<left>.+?)(?:--[^>]*>|==[^>]*>)(?P<right>.+)", line)
    if match is None:
        return None
    left = _normalize_flowchart_node(match.group("left"), node_labels)
    right = _normalize_flowchart_node(match.group("right"), node_labels)
    return f"{left} -> {right}"


def _normalize_flowchart_node(raw_node: str, node_labels: dict[str, str]) -> str:
    cleaned = raw_node.strip()
    alias_match = re.match(r"(?P<id>[A-Za-z0-9_]+)(?P<label>.*)", cleaned)
    if alias_match is None:
        return cleaned
    node_id = alias_match.group("id")
    label = alias_match.group("label").strip()
    if not label:
        return node_labels.get(node_id, node_id)
    label = re.sub(r"^[\[\(\{]+", "", label)
    label = re.sub(r"[\]\)\}]+$", "", label)
    normalized = label.strip() or node_id
    node_labels[node_id] = normalized
    return normalized


def _summarize_pie(lines: list[str]) -> str:
    title_line = lines[0]
    title = title_line.removeprefix("pie").strip()
    values: list[tuple[str, str]] = []
    for raw_line in lines[1:]:
        match = re.match(r'"(?P<label>[^"]+)"\s*:\s*(?P<value>.+)', raw_line)
        if match is None:
            continue
        values.append((match.group("label"), match.group("value").strip()))
    if not values:
        return f"Pie {title or 'chart'}\nNo se pudieron extraer valores legibles."
    summary_lines = [f"Pie {title or 'chart'}", *[f"- {label}: {value}" for label, value in values[:10]]]
    if len(values) > 10:
        summary_lines.append(f"... y {len(values) - 10} segmentos mas.")
    return "\n".join(summary_lines)
