"""Project discovery for Markdown files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mdscope.core.models import ProjectContext, ProjectDocument, ProjectTreeNode

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown"}


@dataclass
class _TreeBuilderNode:
    name: str
    path: Path
    kind: str
    children: dict[str, "_TreeBuilderNode"] = field(default_factory=dict)


def is_markdown_file(path: Path) -> bool:
    """Return whether the given path looks like a Markdown document."""
    return path.is_file() and path.suffix.lower() in MARKDOWN_SUFFIXES


def discover_markdown_files(root: Path) -> tuple[ProjectDocument, ...]:
    """Discover Markdown files under the given project root."""
    documents: list[ProjectDocument] = []
    for path in sorted(root.rglob("*")):
        if not is_markdown_file(path):
            continue
        documents.append(ProjectDocument(path=path, relative_path=path.relative_to(root)))
    return tuple(documents)


def resolve_project_context(target: Path) -> ProjectContext:
    """Resolve the project root, discovered documents, and initial selection."""
    if target.is_dir():
        root = target
        documents = discover_markdown_files(root)
        initial_document = documents[0] if documents else None
        return ProjectContext(
            root=root,
            documents=documents,
            tree=build_project_tree(root, documents),
            initial_document=initial_document,
        )

    root = target.parent
    documents = discover_markdown_files(root)
    initial_document = next((document for document in documents if document.path == target), None)
    if initial_document is None and is_markdown_file(target):
        initial_document = ProjectDocument(path=target, relative_path=Path(target.name))
        documents = (initial_document, *documents)
    deduped_documents = _dedupe_documents(documents)
    initial_document = next(
        (document for document in deduped_documents if document.path == target),
        deduped_documents[0] if deduped_documents else None,
    )
    return ProjectContext(
        root=root,
        documents=deduped_documents,
        tree=build_project_tree(root, deduped_documents),
        initial_document=initial_document,
    )


def _dedupe_documents(
    documents: tuple[ProjectDocument, ...] | list[ProjectDocument],
) -> tuple[ProjectDocument, ...]:
    seen: set[Path] = set()
    unique_documents: list[ProjectDocument] = []
    for document in documents:
        if document.path in seen:
            continue
        seen.add(document.path)
        unique_documents.append(document)
    return tuple(unique_documents)


def build_project_tree(root: Path, documents: tuple[ProjectDocument, ...]) -> ProjectTreeNode:
    """Build a hierarchical tree of directories and Markdown files."""
    builder_root = _TreeBuilderNode(name=root.name or str(root), path=root, kind="directory")
    for document in documents:
        current = builder_root
        parts = document.relative_path.parts
        current_path = root
        for index, part in enumerate(parts):
            current_path = current_path / part
            kind = "file" if index == len(parts) - 1 else "directory"
            if part not in current.children:
                current.children[part] = _TreeBuilderNode(name=part, path=current_path, kind=kind)
            current = current.children[part]
    return _freeze_tree(builder_root)


def _freeze_tree(node: _TreeBuilderNode) -> ProjectTreeNode:
    sorted_children = sorted(
        node.children.values(),
        key=lambda child: (child.kind != "directory", child.name.lower()),
    )
    return ProjectTreeNode(
        name=node.name,
        path=node.path,
        kind=node.kind,
        children=tuple(_freeze_tree(child) for child in sorted_children),
    )
