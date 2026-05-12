"""Textual application for MDScope."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.timer import Timer
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static
from rich.text import Text

from mdscope.adapters.mermaid_cli import MermaidCliAdapter
from mdscope.core.capabilities import detect_terminal_capabilities
from mdscope.core.markdown_parser import extract_section_text, parse_markdown_document
from mdscope.core.models import ProjectTreeNode, SearchResult
from mdscope.core.project_loader import resolve_project_context
from mdscope.renderers.image_renderer import resolve_image_path
from mdscope.renderers.markdown_renderer import render_empty_preview, render_markdown_preview
from mdscope.services.file_watcher import FileWatcher
from mdscope.services.search_index import SearchIndex

_MERMAID_BLOCK_PATTERN = re.compile(r"```mermaid[^\n]*\n(?P<body>.*?)\n```", re.DOTALL)
_IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)")


class PreviewPane(VerticalScroll):
    """Scrollable preview container with explicit keyboard controls."""

    BINDINGS = [
        ("up,k", "cursor_up", "Up"),
        ("down,j", "cursor_down", "Down"),
        ("pageup", "page_up", "Page up"),
        ("pagedown", "page_down", "Page down"),
        ("home", "scroll_home", "Top"),
        ("end", "scroll_end", "Bottom"),
    ]

    def action_cursor_up(self) -> None:
        self.scroll_relative(y=-3, animate=False)

    def action_cursor_down(self) -> None:
        self.scroll_relative(y=3, animate=False)

    def action_page_up(self) -> None:
        self.scroll_page_up(animate=False)

    def action_page_down(self) -> None:
        self.scroll_page_down(animate=False)

    def action_scroll_home(self) -> None:
        self.scroll_home(animate=False)

    def action_scroll_end(self) -> None:
        self.scroll_end(animate=False)


class PreviewContent(Static):
    """Rich renderable holder mounted inside the preview scroll container."""


class MDScopeApp(App[None]):
    """TUI shell with explorer, preview, TOC and project search."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #search-bar {
        margin: 0 1;
    }

    #body {
        height: 1fr;
    }

    .panel {
        height: 1fr;
        border: round $surface;
        padding: 1 2;
    }

    #explorer {
        width: 26;
    }

    #preview {
        width: 1fr;
        overflow-y: auto;
        overflow-x: auto;
    }

    #preview:focus {
        border: round $accent;
    }

    #sidebar {
        width: 34;
    }

    ListView {
        background: $panel;
    }
    """

    BINDINGS = [
        ("/", "focus_search", "Search"),
        ("tab", "focus_next_panel", "Next panel"),
        ("shift+tab", "focus_previous_panel", "Prev panel"),
        ("enter", "activate_explorer_selection", "Open/toggle"),
        ("right", "expand_explorer_directory", "Expand dir"),
        ("left", "collapse_explorer_directory", "Collapse dir"),
        ("r", "refresh_document", "Refresh"),
        ("f", "show_full_document", "Full doc"),
        ("o", "open_preview_asset", "Open image"),
        ("escape", "clear_search", "Clear search"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, initial_target: Path) -> None:
        super().__init__()
        self.initial_target = initial_target
        self.project = resolve_project_context(initial_target)
        self.capabilities = detect_terminal_capabilities()
        self.mermaid_adapter = MermaidCliAdapter()
        self.active_document = self.project.initial_document
        self.active_heading_anchor: str | None = None
        self.search_query = ""
        self.search_results: tuple[SearchResult, ...] = ()
        self.search_index = SearchIndex()
        self.search_index.index_documents(self.project.documents)
        self.file_watcher = FileWatcher(self.project.root, self._handle_filesystem_change)
        self.pending_change_path: Path | None = None
        self.reload_timer: Timer | None = None
        self._suppress_explorer_selection = False
        self._suppress_sidebar_selection = False
        self.expanded_directories = {self.project.root}
        self.parsed_document = (
            parse_markdown_document(self.active_document.path)
            if self.active_document is not None
            else None
        )
        self._expand_active_document_ancestors()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Input(placeholder="Buscar en el proyecto...", id="search-bar")
            with Horizontal(id="body"):
                yield ListView(id="explorer", classes="panel")
                with PreviewPane(id="preview", classes="panel"):
                    yield PreviewContent("", id="preview-content")
                yield ListView(id="sidebar", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the initial UI."""
        self.title = "MDScope"
        self.sub_title = str(self.project.root)

        explorer = self.query_one("#explorer", ListView)
        explorer.border_title = "Explorador"
        self.query_one("#preview", PreviewPane).border_title = "Preview"
        sidebar = self.query_one("#sidebar", ListView)
        sidebar.border_title = "TOC"

        self._refresh_explorer_list()
        self._refresh_panels()
        explorer.focus()
        self.file_watcher.start()

        if self.active_document is not None:
            self._set_sidebar_index(sidebar, 0)

    def on_unmount(self) -> None:
        """Stop filesystem watching when the app exits."""
        self.file_watcher.stop()

    @on(ListView.Selected, "#explorer")
    def handle_document_selected(self, event: ListView.Selected) -> None:
        """Update the active document when explorer selection changes."""
        if self._suppress_explorer_selection:
            return
        if event.item.name is None:
            return
        self._activate_explorer_item(event.item.name)

    @on(ListView.Selected, "#sidebar")
    def handle_sidebar_selected(self, event: ListView.Selected) -> None:
        """Handle TOC or search-result selection."""
        if self._suppress_sidebar_selection:
            return
        if event.item.name is None:
            return
        if event.item.name == "__full__":
            self.active_heading_anchor = None
            self._refresh_panels()
            return
        if event.item.name.startswith("toc:"):
            self.active_heading_anchor = event.item.name.removeprefix("toc:")
            self._refresh_panels()
            return
        if event.item.name.startswith("search:"):
            self._activate_search_result(event.item.name.removeprefix("search:"))

    @on(Input.Changed, "#search-bar")
    def handle_search_changed(self, event: Input.Changed) -> None:
        """Update project search results as the query changes."""
        self.search_query = event.value
        self.search_results = self.search_index.search(event.value)
        self._refresh_panels()

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-bar", Input).focus()

    def action_clear_search(self) -> None:
        """Clear the search query and restore TOC mode."""
        search_bar = self.query_one("#search-bar", Input)
        if not self.search_query and not search_bar.value:
            return
        search_bar.value = ""
        self.search_query = ""
        self.search_results = ()
        self._refresh_panels()

    def action_focus_next_panel(self) -> None:
        """Move focus between explorer, preview, sidebar and search."""
        widgets = [
            self.query_one("#explorer", ListView),
            self.query_one("#preview", PreviewPane),
            self.query_one("#sidebar", ListView),
            self.query_one("#search-bar", Input),
        ]
        self._cycle_focus(widgets, direction=1)

    def action_focus_previous_panel(self) -> None:
        """Move focus backwards between explorer, preview, sidebar and search."""
        widgets = [
            self.query_one("#explorer", ListView),
            self.query_one("#preview", PreviewPane),
            self.query_one("#sidebar", ListView),
            self.query_one("#search-bar", Input),
        ]
        self._cycle_focus(widgets, direction=-1)

    def action_activate_explorer_selection(self) -> None:
        """Toggle the selected directory or open the selected file."""
        if self.focused is not self.query_one("#explorer", ListView):
            return
        explorer = self.query_one("#explorer", ListView)
        if explorer.index is None or explorer.index < 0 or explorer.index >= len(explorer.children):
            return
        selected_item = list(explorer.children)[explorer.index]
        if selected_item.name is None:
            return
        self._activate_explorer_item(selected_item.name)

    def action_expand_explorer_directory(self) -> None:
        """Expand the selected directory when the explorer is focused."""
        if self.focused is not self.query_one("#explorer", ListView):
            return
        item_name = self._get_selected_explorer_name()
        if item_name is None or not item_name.startswith("dir:"):
            return
        directory_path = Path(item_name.removeprefix("dir:"))
        if directory_path in self.expanded_directories:
            return
        self.expanded_directories.add(directory_path)
        self._refresh_explorer_list(selected_name=item_name)

    def action_collapse_explorer_directory(self) -> None:
        """Collapse the selected directory or its parent when the explorer is focused."""
        if self.focused is not self.query_one("#explorer", ListView):
            return
        item_name = self._get_selected_explorer_name()
        if item_name is None:
            return
        if item_name.startswith("dir:"):
            directory_path = Path(item_name.removeprefix("dir:"))
            if directory_path in self.expanded_directories and directory_path != self.project.root:
                self.expanded_directories.discard(directory_path)
                self._refresh_explorer_list(selected_name=item_name)
                return
        if item_name.startswith("file:"):
            node_path = Path(item_name.removeprefix("file:"))
        else:
            node_path = Path(item_name.removeprefix("dir:"))
        parent = node_path.parent
        if parent == self.project.root:
            return
        self.expanded_directories.discard(parent)
        self._refresh_explorer_list(selected_name=f"dir:{parent}")

    def action_refresh_document(self) -> None:
        """Reparse the active document and rebuild search state."""
        self._reload_project_state()

    def action_show_full_document(self) -> None:
        """Reset preview to the full-document view."""
        self.active_heading_anchor = None
        sidebar = self.query_one("#sidebar", ListView)
        if len(sidebar.children) > 0:
            self._set_sidebar_index(sidebar, 0)
        self._refresh_panels()

    def action_open_preview_asset(self) -> None:
        """Open the first image-like asset from the active preview using the OS viewer."""
        asset_path = self._resolve_preview_asset_path()
        if asset_path is None:
            self._notify_user("No hay imagen o Mermaid abrible en el preview actual.", severity="warning")
            return
        if not asset_path.exists():
            self._notify_user(f"No existe el archivo: {asset_path}", severity="error")
            return
        if not self._open_path_in_system_viewer(asset_path):
            self._notify_user(
                "No se encontro un visor compatible. Instala `xdg-open`, `open` o `start`.",
                severity="error",
            )
            return
        self._notify_user(f"Abriendo imagen: {asset_path.name}")

    def _activate_search_result(self, relative_key: str) -> None:
        result = next(
            (item for item in self.search_results if str(item.relative_path) == relative_key),
            None,
        )
        if result is None:
            return
        self.active_document = next(
            (document for document in self.project.documents if document.path == result.path),
            None,
        )
        if self.active_document is None:
            return
        self._expand_active_document_ancestors()
        self.active_heading_anchor = result.anchor
        self.parsed_document = parse_markdown_document(self.active_document.path)
        explorer = self.query_one("#explorer", ListView)
        self._set_explorer_selection_by_path(explorer, result.path)
        self._refresh_panels()

    def _handle_filesystem_change(self, changed_path: Path) -> None:
        """Bridge watchdog changes back into the Textual app thread."""
        self.pending_change_path = changed_path
        self.call_from_thread(self._schedule_reload)

    def _schedule_reload(self) -> None:
        """Debounce reload work to avoid duplicate refresh storms."""
        if self.reload_timer is not None:
            self.reload_timer.stop()
        self.reload_timer = self.set_timer(0.2, self._reload_project_state)

    def _reload_project_state(self) -> None:
        """Reload project discovery, active document and search index."""
        previous_active_path = (
            self.active_document.path if self.active_document is not None else None
        )
        self.project = resolve_project_context(self.project.root)
        self.search_index.index_documents(self.project.documents)

        if previous_active_path is not None:
            self.active_document = next(
                (
                    document
                    for document in self.project.documents
                    if document.path == previous_active_path
                ),
                self.project.initial_document,
            )
        else:
            self.active_document = self.project.initial_document

        if self.active_document is None:
            self.parsed_document = None
            self.active_heading_anchor = None
        else:
            self._expand_active_document_ancestors()
            self.parsed_document = parse_markdown_document(self.active_document.path)
            if self.active_heading_anchor is not None and self.parsed_document is not None:
                anchors = {heading.anchor for heading in self.parsed_document.headings}
                if self.active_heading_anchor not in anchors:
                    self.active_heading_anchor = None

        if self.search_query:
            self.search_results = self.search_index.search(self.search_query)
        else:
            self.search_results = ()

        self._refresh_explorer_list()
        self._refresh_panels()

    def _refresh_explorer_list(self, *, selected_name: str | None = None) -> None:
        explorer = self.query_one("#explorer", ListView)
        explorer.clear()
        for node, depth in self._iter_visible_tree_nodes():
            explorer.append(ListItem(Label(self._format_tree_label(node, depth)), name=self._node_item_name(node)))
        if selected_name is not None:
            self._set_explorer_selection_by_name(explorer, selected_name)
            return
        if self.active_document is None:
            return
        self._set_explorer_selection_by_path(explorer, self.active_document.path)

    def _refresh_panels(self) -> None:
        preview = self.query_one("#preview", PreviewPane)
        preview_content = self.query_one("#preview-content", PreviewContent)
        sidebar = self.query_one("#sidebar", ListView)
        sidebar.border_title = "Busqueda" if self.search_query.strip() else "TOC"
        preview_content.update(self._build_preview_renderable())
        self._reset_preview_scroll(preview)
        self._refresh_sidebar_list(sidebar)

    def _build_preview_renderable(self) -> Any:
        if self.active_document is None:
            return render_empty_preview(str(self.project.root))
        if self.parsed_document is None:
            return render_empty_preview(str(self.project.root))
        return render_markdown_preview(
            self.active_document,
            self.parsed_document,
            self.capabilities,
            active_anchor=self.active_heading_anchor,
            mermaid_adapter=self.mermaid_adapter,
        )

    def _refresh_sidebar_list(self, sidebar: ListView) -> None:
        if self.search_query.strip():
            self._refresh_search_results_list(sidebar)
            return
        self._refresh_toc_list(sidebar)

    def _refresh_search_results_list(self, sidebar: ListView) -> None:
        sidebar.clear()
        if not self.search_results:
            sidebar.append(ListItem(Label("Sin resultados"), name="__search_empty__"))
            return
        for result in self.search_results[:25]:
            heading = f" -> {result.heading}" if result.heading else ""
            label = f"{result.relative_path}{heading}"
            sidebar.append(ListItem(Label(label), name=f"search:{result.relative_path}"))
        self._set_sidebar_index(sidebar, 0)

    def _refresh_toc_list(self, sidebar: ListView) -> None:
        sidebar.clear()
        if self.active_document is None or self.parsed_document is None:
            sidebar.append(ListItem(Label("Sin documento cargado"), name="__full__"))
            return
        sidebar.append(ListItem(Label("Documento completo"), name="__full__"))
        for heading in self.parsed_document.headings[:50]:
            indent = "  " * max(heading.level - 1, 0)
            sidebar.append(
                ListItem(Label(f"{indent}{heading.text}"), name=f"toc:{heading.anchor}")
            )

        if self.active_heading_anchor is None:
            self._set_sidebar_index(sidebar, 0)
            return

        for index, item in enumerate(list(sidebar.children)):
            if item.name == f"toc:{self.active_heading_anchor}":
                self._set_sidebar_index(sidebar, index)
                break

    def _cycle_focus(self, widgets: list[Any], direction: int) -> None:
        focused = self.focused
        if focused in widgets:
            current_index = widgets.index(focused)
            next_index = (current_index + direction) % len(widgets)
        else:
            next_index = 0
        widgets[next_index].focus()

    def _set_explorer_index(self, explorer: ListView, index: int) -> None:
        """Update explorer selection without retriggering handlers."""
        if explorer.index == index:
            return
        self._suppress_explorer_selection = True
        try:
            explorer.index = index
        finally:
            self._suppress_explorer_selection = False

    def _set_sidebar_index(self, sidebar: ListView, index: int) -> None:
        """Update sidebar selection without retriggering handlers."""
        if sidebar.index == index:
            return
        self._suppress_sidebar_selection = True
        try:
            sidebar.index = index
        finally:
            self._suppress_sidebar_selection = False

    def _activate_explorer_item(self, item_name: str) -> None:
        if item_name.startswith("dir:"):
            directory_path = Path(item_name.removeprefix("dir:"))
            if directory_path in self.expanded_directories:
                if directory_path != self.project.root:
                    self.expanded_directories.discard(directory_path)
            else:
                self.expanded_directories.add(directory_path)
            self._refresh_explorer_list(selected_name=item_name)
            return
        if not item_name.startswith("file:"):
            return
        selected_path = Path(item_name.removeprefix("file:"))
        self.active_document = next(
            (document for document in self.project.documents if document.path == selected_path),
            None,
        )
        self.active_heading_anchor = None
        self.parsed_document = (
            parse_markdown_document(self.active_document.path)
            if self.active_document is not None
            else None
        )
        self._refresh_panels()

    def _iter_visible_tree_nodes(self) -> list[tuple[ProjectTreeNode, int]]:
        visible_nodes: list[tuple[ProjectTreeNode, int]] = []

        def visit(node: ProjectTreeNode, depth: int) -> None:
            for child in node.children:
                visible_nodes.append((child, depth))
                if child.kind == "directory" and child.path in self.expanded_directories:
                    visit(child, depth + 1)

        visit(self.project.tree, 0)
        return visible_nodes

    def _format_tree_label(self, node: ProjectTreeNode, depth: int) -> Text:
        label = Text()
        indent = "  " * depth
        if indent:
            label.append(indent, style="dim")
        if node.kind == "directory":
            icon = "▾" if node.path in self.expanded_directories else "▸"
            label.append(f"{icon} ", style="bright_black")
            label.append(f"{node.name}/", style=self._directory_style(depth))
            return label
        label.append("• ", style="bright_black")
        file_style = "bright_white" if depth == 0 else "white"
        label.append(node.name, style=file_style)
        return label

    def _node_item_name(self, node: ProjectTreeNode) -> str:
        prefix = "dir" if node.kind == "directory" else "file"
        return f"{prefix}:{node.path}"

    def _directory_style(self, depth: int) -> str:
        if depth == 0:
            return "bold cyan"
        if depth == 1:
            return "blue"
        return "green"

    def _set_explorer_selection_by_path(self, explorer: ListView, path: Path) -> None:
        target_name = f"file:{path}"
        self._set_explorer_selection_by_name(explorer, target_name)

    def _set_explorer_selection_by_name(self, explorer: ListView, item_name: str) -> None:
        target_name = item_name
        for index, item in enumerate(list(explorer.children)):
            if item.name == target_name:
                self._set_explorer_index(explorer, index)
                break

    def _expand_active_document_ancestors(self) -> None:
        if self.active_document is None:
            return
        for ancestor in self.active_document.path.parents:
            if ancestor == self.project.root:
                self.expanded_directories.add(ancestor)
                break
            if self.project.root in ancestor.parents:
                self.expanded_directories.add(ancestor)

    def _get_selected_explorer_name(self) -> str | None:
        explorer = self.query_one("#explorer", ListView)
        if explorer.index is None or explorer.index < 0 or explorer.index >= len(explorer.children):
            return None
        selected_item = list(explorer.children)[explorer.index]
        return selected_item.name

    def _reset_preview_scroll(self, preview: PreviewPane | None = None) -> None:
        active_preview = preview or self.query_one("#preview", PreviewPane)
        active_preview.scroll_to(0, 0, animate=False, force=True)

    def _resolve_preview_asset_path(self) -> Path | None:
        if self.active_document is None or self.parsed_document is None:
            return None
        section_text = extract_section_text(self.parsed_document, self.active_heading_anchor)
        candidates: list[tuple[int, str, str]] = []

        for match in _MERMAID_BLOCK_PATTERN.finditer(section_text):
            candidates.append((match.start(), "mermaid", match.group("body")))
        for match in _IMAGE_PATTERN.finditer(section_text):
            candidates.append((match.start(), "image", match.group("target")))

        if not candidates:
            return None

        _, asset_kind, payload = min(candidates, key=lambda item: item[0])
        if asset_kind == "mermaid":
            result = self.mermaid_adapter.render_to_png(payload.strip())
            return result.image_path if result.status == "rendered" else None

        return resolve_image_path(payload, self.active_document.path)

    def _open_path_in_system_viewer(self, path: Path) -> bool:
        command = self._viewer_command(path)
        if command is None:
            return False
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True

    def _viewer_command(self, path: Path) -> list[str] | None:
        if sys.platform == "darwin":
            return ["open", str(path)]
        if sys.platform.startswith("win"):
            return ["cmd", "/c", "start", "", str(path)]
        opener = shutil.which("xdg-open")
        if opener is None:
            return None
        return [opener, str(path)]

    def _notify_user(self, message: str, *, severity: str = "information") -> None:
        notify = getattr(self, "notify", None)
        if callable(notify):
            notify(message, severity=severity)
