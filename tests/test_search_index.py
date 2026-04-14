from __future__ import annotations

from pathlib import Path

from mdscope.core.models import ProjectDocument
from mdscope.services.search_index import SearchIndex


def test_search_index_finds_document_content(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Intro\n\nBusqueda local con SQLite.\n", encoding="utf-8")
    documents = (ProjectDocument(path=readme, relative_path=Path("README.md")),)

    index = SearchIndex()
    index.index_documents(documents)
    results = index.search("SQLite")

    assert results
    assert results[0].relative_path == Path("README.md")


def test_search_index_returns_heading_anchors(tmp_path: Path) -> None:
    guide = tmp_path / "guide.md"
    guide.write_text("# Intro\n\n## Arquitectura\n\nTexto.\n", encoding="utf-8")
    documents = (ProjectDocument(path=guide, relative_path=Path("guide.md")),)

    index = SearchIndex()
    index.index_documents(documents)
    results = index.search("Arquitectura")

    assert any(result.anchor == "arquitectura" for result in results)


def test_search_index_handles_unreadable_document_reference(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    documents = (ProjectDocument(path=missing, relative_path=Path("missing.md")),)

    index = SearchIndex()
    index.index_documents(documents)
    results = index.search("Error")

    assert results
    assert results[0].relative_path == Path("missing.md")
