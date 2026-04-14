from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.widgets import Input, ListView

from mdscope.ui.app import MDScopeApp


def test_app_stores_initial_target() -> None:
    target = Path.cwd().resolve()

    app = MDScopeApp(initial_target=target)

    assert app.initial_target == target


@pytest.mark.asyncio
async def test_app_mounts_and_populates_explorer(tmp_path: Path, monkeypatch: Any) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Intro\n", encoding="utf-8")

    monkeypatch.setattr("mdscope.ui.app.FileWatcher.start", lambda self: None)
    monkeypatch.setattr("mdscope.ui.app.FileWatcher.stop", lambda self: None)

    app = MDScopeApp(initial_target=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()
        explorer = app.query_one("#explorer", ListView)
        assert len(explorer.children) == 1


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
