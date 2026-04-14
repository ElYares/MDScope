"""Filesystem watching for Markdown project changes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

from mdscope.core.project_loader import MARKDOWN_SUFFIXES


class MarkdownChangeHandler(FileSystemEventHandler):
    """Forward relevant Markdown file changes to the provided callback."""

    def __init__(self, callback: Callable[[Path], None]) -> None:
        self.callback = callback

    def on_modified(self, event: FileSystemEvent) -> None:
        self._forward_if_relevant(event)

    def on_created(self, event: FileSystemEvent) -> None:
        self._forward_if_relevant(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._forward_if_relevant(event)

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        self._forward_if_relevant(event)

    def _forward_if_relevant(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        candidate_paths = [self._path_from_event_value(event.src_path)]
        if isinstance(event, FileSystemMovedEvent):
            candidate_paths.append(self._path_from_event_value(event.dest_path))
        for changed_path in candidate_paths:
            if changed_path.suffix.lower() not in MARKDOWN_SUFFIXES:
                continue
            self.callback(changed_path)

    def _path_from_event_value(self, raw_path: str | bytes) -> Path:
        resolved = raw_path.decode() if isinstance(raw_path, bytes) else raw_path
        return Path(resolved)


class FileWatcher:
    """Manage a watchdog observer for the active project root."""

    def __init__(self, root: Path, on_change: Callable[[Path], None]) -> None:
        self.root = root
        self.on_change = on_change
        self.observer = Observer()
        self.handler = MarkdownChangeHandler(on_change)
        self._started = False

    def start(self) -> None:
        """Start observing the project root recursively."""
        if self._started:
            return
        self.observer.schedule(self.handler, str(self.root), recursive=True)
        self.observer.start()
        self._started = True

    def stop(self) -> None:
        """Stop the observer if it is running."""
        if not self._started:
            return
        self.observer.stop()
        self.observer.join(timeout=1.0)
        self._started = False
