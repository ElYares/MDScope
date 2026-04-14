from __future__ import annotations

from pathlib import Path

from mdscope.core.project_loader import discover_markdown_files, resolve_project_context


def test_discover_markdown_files_ignores_non_markdown(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("# A\n", encoding="utf-8")
    (docs_dir / "b.markdown").write_text("# B\n", encoding="utf-8")
    (docs_dir / "notes.txt").write_text("ignore\n", encoding="utf-8")

    documents = discover_markdown_files(tmp_path)

    assert [str(document.relative_path) for document in documents] == [
        "docs/a.md",
        "docs/b.markdown",
    ]


def test_resolve_project_context_from_directory(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")

    context = resolve_project_context(tmp_path)

    assert context.root == tmp_path
    assert len(context.documents) == 2
    assert context.initial_document is not None
    assert context.initial_document.relative_path == Path("README.md")


def test_resolve_project_context_from_file_keeps_selected_document(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    guide = tmp_path / "guide.md"
    readme.write_text("# Home\n", encoding="utf-8")
    guide.write_text("# Guide\n", encoding="utf-8")

    context = resolve_project_context(guide)

    assert context.root == tmp_path
    assert context.initial_document is not None
    assert context.initial_document.path == guide
