"""Domain models for project discovery and Markdown parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectDocument:
    """A Markdown document discovered inside the active project."""

    path: Path
    relative_path: Path


@dataclass(frozen=True)
class ProjectContext:
    """Resolved project root and active document state."""

    root: Path
    documents: tuple[ProjectDocument, ...]
    initial_document: ProjectDocument | None


@dataclass(frozen=True)
class Heading:
    """A heading extracted from a Markdown document."""

    level: int
    text: str
    anchor: str
    start_line: int
    end_line: int | None = None


@dataclass(frozen=True)
class RenderBlock:
    """A parsed block from a Markdown document."""

    kind: str
    text: str
    info: str | None = None
    meta: str | None = None


@dataclass(frozen=True)
class ParsedDocument:
    """Structured representation of a Markdown document."""

    source_path: Path
    raw_text: str
    headings: tuple[Heading, ...]
    blocks: tuple[RenderBlock, ...]


@dataclass(frozen=True)
class SearchResult:
    """A search result returned by the local SQLite index."""

    path: Path
    relative_path: Path
    title: str
    anchor: str | None
    heading: str | None
    snippet: str
