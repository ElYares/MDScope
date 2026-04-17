from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input, ListView

from mdscope.ui.app import MDScopeApp, PreviewPane


def test_app_stores_initial_target() -> None:
    target = Path.cwd().resolve()

    app = MDScopeApp(initial_target=target)

    assert app.initial_target == target


@pytest.mark.asyncio
async def test_app_mounts_and_populates_explorer(tmp_path: Path, monkeypatch: Any) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    readme = tmp_path / "README.md"
    guide = docs_dir / "guide.md"
    readme.write_text("# Intro\n", encoding="utf-8")
    guide.write_text("# Guide\n", encoding="utf-8")

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()
        explorer = app.query_one("#explorer", ListView)
        item_names = [item.name for item in explorer.children]
        assert len(explorer.children) == 2
        assert item_names == [f"dir:{docs_dir}", f"file:{readme}"]


@pytest.mark.asyncio
async def test_search_updates_sidebar_results(tmp_path: Path, monkeypatch: Any) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Intro\n\nSQLite search works.\n", encoding="utf-8")

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        search_bar = app.query_one("#search-bar", Input)
        search_bar.value = "SQLite"
        await pilot.pause()
        sidebar = app.query_one("#sidebar", ListView)
        assert len(sidebar.children) >= 1


@pytest.mark.asyncio
async def test_explorer_expands_directory_and_opens_nested_file(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    guide = docs_dir / "guide.md"
    guide.write_text("# Guide\n\nNested content.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Home\n", encoding="utf-8")

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()
        explorer = app.query_one("#explorer", ListView)
        app._activate_explorer_item(f"dir:{docs_dir}")
        await pilot.pause()

        item_names = [item.name for item in explorer.children]
        assert item_names == [f"dir:{docs_dir}", f"file:{guide}", f"file:{tmp_path / 'README.md'}"]

        app._activate_explorer_item(f"file:{guide}")
        await pilot.pause()

        assert app.active_document is not None
        assert app.active_document.path == guide


@pytest.mark.asyncio
async def test_preview_resets_scroll_when_switching_to_toc_section(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Intro\n\n" + "\n".join(f"Linea {index}" for index in range(80)) + "\n\n## Uso\n\nContenido uso\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()
        preview = app.query_one("#preview", PreviewPane)
        preview.scroll_to(0, 200, animate=False, force=True)
        await pilot.pause()

        assert preview.scroll_y > 0

        app.active_heading_anchor = "uso"
        app._refresh_panels()
        await pilot.pause()

        assert preview.scroll_y == 0


@pytest.mark.asyncio
async def test_preview_resets_scroll_when_returning_to_full_document(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Intro\n\n## Uso\n\n" + "\n".join(f"Paso {index}" for index in range(80)),
        encoding="utf-8",
    )

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()
        preview = app.query_one("#preview", PreviewPane)

        app.active_heading_anchor = "uso"
        app._refresh_panels()
        await pilot.pause()

        preview.scroll_to(0, 200, animate=False, force=True)
        await pilot.pause()
        assert preview.scroll_y > 0

        app.action_show_full_document()
        await pilot.pause()

        assert preview.scroll_y == 0


@pytest.mark.asyncio
async def test_preview_can_receive_focus_for_scrolling(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Intro\n\nTexto\n", encoding="utf-8")

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()
        app.action_focus_next_panel()
        await pilot.pause()

        preview = app.query_one("#preview", PreviewPane)
        assert app.focused is preview
