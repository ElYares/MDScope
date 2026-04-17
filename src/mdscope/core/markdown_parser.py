"""Markdown parsing helpers."""

from __future__ import annotations

import re
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from mdscope.core.models import Heading, ParsedDocument, RenderBlock

_ANCHOR_RE = re.compile(r"[^a-z0-9]+")
_IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)")
_parser = MarkdownIt("commonmark")
_SPECIAL_FENCE_KINDS = {
    "mermaid": "mermaid",
    "chart": "chart",
    "math": "math",
    "table": "table",
    "matrix": "matrix",
}


def parse_markdown_document(source_path: Path) -> ParsedDocument:
    """Parse a Markdown file into structured blocks and headings."""
    try:
        raw_text = source_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ParsedDocument(
            source_path=source_path,
            raw_text=f"# Error de lectura\n\nNo se pudo leer `{source_path}`.\n\n{exc}",
            headings=(),
            blocks=(RenderBlock(kind="error", text=str(exc)),),
        )
    return parse_markdown_text(source_path=source_path, raw_text=raw_text)


def parse_markdown_text(source_path: Path, raw_text: str) -> ParsedDocument:
    """Parse Markdown text into a reusable document model."""
    tokens = _parser.parse(raw_text)
    headings = tuple(_extract_headings(tokens))
    blocks = tuple(_extract_blocks(tokens))
    return ParsedDocument(
        source_path=source_path,
        raw_text=raw_text,
        headings=headings,
        blocks=blocks,
    )


def _extract_headings(tokens: list[Token]) -> list[Heading]:
    headings: list[Heading] = []
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        level = int(token.tag[1])
        inline_token = tokens[index + 1]
        text = inline_token.content.strip()
        if not text:
            continue
        line_map = token.map or [0, 0]
        headings.append(
            Heading(
                level=level,
                text=text,
                anchor=_slugify(text),
                start_line=line_map[0],
            )
        )
    return _assign_heading_ranges(headings)


def _extract_blocks(tokens: list[Token]) -> list[RenderBlock]:
    blocks: list[RenderBlock] = []
    for token in tokens:
        if token.type == "fence":
            info = token.info.strip() or None
            kind = _classify_fence_kind(info)
            blocks.append(RenderBlock(kind=kind, text=token.content, info=info))
            continue
        if token.type == "inline" and token.content.strip():
            blocks.extend(_extract_inline_blocks(token.content.strip()))
            continue
        if token.type == "paragraph_open":
            blocks.append(RenderBlock(kind="paragraph", text=""))
            continue
        if token.type == "bullet_list_open":
            blocks.append(RenderBlock(kind="bullet_list", text=""))
            continue
        if token.type == "ordered_list_open":
            blocks.append(RenderBlock(kind="ordered_list", text=""))
            continue
    return blocks


def _classify_fence_kind(info: str | None) -> str:
    if info is None:
        return "fence"
    fence_name = info.split(maxsplit=1)[0].lower()
    return _SPECIAL_FENCE_KINDS.get(fence_name, "fence")


def _extract_inline_blocks(text: str) -> list[RenderBlock]:
    images = [
        RenderBlock(kind="image", text=match.group("target"), meta=match.group("alt") or None)
        for match in _IMAGE_RE.finditer(text)
    ]
    if images:
        return images
    return [RenderBlock(kind="inline", text=text)]


def _slugify(text: str) -> str:
    normalized = text.strip().lower()
    slug = _ANCHOR_RE.sub("-", normalized).strip("-")
    return slug or "section"


def _assign_heading_ranges(headings: list[Heading]) -> list[Heading]:
    ranged_headings: list[Heading] = []
    for index, heading in enumerate(headings):
        next_heading = headings[index + 1] if index + 1 < len(headings) else None
        end_line = next_heading.start_line if next_heading is not None else None
        ranged_headings.append(
            Heading(
                level=heading.level,
                text=heading.text,
                anchor=heading.anchor,
                start_line=heading.start_line,
                end_line=end_line,
            )
        )
    return ranged_headings


def extract_section_text(parsed_document: ParsedDocument, anchor: str | None) -> str:
    """Extract a heading section from a parsed document."""
    if anchor is None:
        return parsed_document.raw_text
    heading = next((item for item in parsed_document.headings if item.anchor == anchor), None)
    if heading is None:
        return parsed_document.raw_text
    lines = parsed_document.raw_text.splitlines()
    end_line = heading.end_line if heading.end_line is not None else len(lines)
    section_lines = lines[heading.start_line:end_line]
    section_text = "\n".join(section_lines).strip()
    return section_text or heading.text
