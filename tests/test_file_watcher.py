from __future__ import annotations

from pathlib import Path

from watchdog.events import FileModifiedEvent, FileMovedEvent, FileOpenedEvent

from mdscope.services.file_watcher import MarkdownChangeHandler


def test_markdown_change_handler_ignores_non_markdown_files(tmp_path: Path) -> None:
    captured: list[Path] = []
    handler = MarkdownChangeHandler(captured.append)

    handler.on_modified(FileModifiedEvent(str(tmp_path / "notes.txt")))

    assert captured == []


def test_markdown_change_handler_forwards_markdown_files(tmp_path: Path) -> None:
    captured: list[Path] = []
    handler = MarkdownChangeHandler(captured.append)

    handler.on_modified(FileModifiedEvent(str(tmp_path / "README.md")))

    assert captured == [tmp_path / "README.md"]


def test_markdown_change_handler_ignores_file_open_events(tmp_path: Path) -> None:
    captured: list[Path] = []
    handler = MarkdownChangeHandler(captured.append)

    handler.dispatch(FileOpenedEvent(str(tmp_path / "README.md")))

    assert captured == []


def test_markdown_change_handler_forwards_markdown_move_destinations(tmp_path: Path) -> None:
    captured: list[Path] = []
    handler = MarkdownChangeHandler(captured.append)

    handler.on_moved(FileMovedEvent(str(tmp_path / "README.txt"), str(tmp_path / "README.md")))

    assert captured == [tmp_path / "README.md"]
