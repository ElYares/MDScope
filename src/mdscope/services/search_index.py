"""SQLite FTS5 search service."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mdscope.core.markdown_parser import parse_markdown_document
from mdscope.core.models import ProjectDocument, SearchResult


class SearchIndex:
    """Project-local in-memory SQLite FTS5 index."""

    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE VIRTUAL TABLE search_index USING fts5(
                path UNINDEXED,
                relative_path UNINDEXED,
                title,
                heading,
                anchor UNINDEXED,
                content
            )
            """
        )
        self.connection.commit()

    def index_documents(self, documents: tuple[ProjectDocument, ...]) -> None:
        """Rebuild the FTS index for the active project."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM search_index")
        for document in documents:
            parsed = parse_markdown_document(document.path)
            title = parsed.headings[0].text if parsed.headings else document.relative_path.stem
            headings_text = "\n".join(heading.text for heading in parsed.headings)
            cursor.execute(
                """
                INSERT INTO search_index(path, relative_path, title, heading, anchor, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(document.path),
                    str(document.relative_path),
                    title,
                    headings_text,
                    None,
                    parsed.raw_text,
                ),
            )
            for heading in parsed.headings:
                cursor.execute(
                    """
                    INSERT INTO search_index(path, relative_path, title, heading, anchor, content)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(document.path),
                        str(document.relative_path),
                        title,
                        heading.text,
                        heading.anchor,
                        parsed.raw_text,
                    ),
                )
        self.connection.commit()

    def search(self, query: str, *, limit: int = 20) -> tuple[SearchResult, ...]:
        """Search indexed content using SQLite FTS5 ranking."""
        normalized = query.strip()
        if not normalized:
            return ()
        cursor = self.connection.cursor()
        rows = cursor.execute(
            """
            SELECT
                path,
                relative_path,
                title,
                heading,
                anchor,
                snippet(search_index, 5, '[', ']', ' … ', 10) AS snippet_text
            FROM search_index
            WHERE search_index MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (normalized, limit),
        ).fetchall()
        return tuple(
            SearchResult(
                path=Path(str(row["path"])),
                relative_path=Path(str(row["relative_path"])),
                title=str(row["title"]),
                anchor=str(row["anchor"]) if row["anchor"] is not None else None,
                heading=str(row["heading"]) if row["heading"] is not None else None,
                snippet=str(row["snippet_text"]),
            )
            for row in rows
        )
