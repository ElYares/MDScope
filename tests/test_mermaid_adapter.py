from __future__ import annotations

import hashlib
from pathlib import Path

from mdscope.adapters.mermaid_cli import MermaidCliAdapter


def test_mermaid_adapter_reports_unavailable_when_cli_missing(tmp_path: Path) -> None:
    adapter = MermaidCliAdapter(cache_root=tmp_path, cli_path=None)

    result = adapter.render_to_png("graph TD\nA-->B\n")

    assert result.status == "unavailable"
    assert result.image_path is None


def test_mermaid_adapter_uses_cached_png(tmp_path: Path) -> None:
    adapter = MermaidCliAdapter(cache_root=tmp_path, cli_path="mmdc")
    digest = hashlib.sha256(b"graph TD\nA-->B\n").hexdigest()[:16]
    cached_png = tmp_path / f"{digest}.png"
    cached_png.write_bytes(b"png")

    result = adapter.render_to_png("graph TD\nA-->B\n")

    assert result.status == "rendered"
    assert result.image_path == cached_png
    assert result.cache_hit is True
