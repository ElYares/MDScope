"""Adapter for Mermaid CLI rendering."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from typing import cast
from dataclasses import dataclass
from pathlib import Path

_AUTO_CLI = object()


@dataclass(frozen=True)
class MermaidRenderResult:
    """Result of attempting to render a Mermaid block."""

    status: str
    image_path: Path | None = None
    message: str | None = None
    cache_hit: bool = False


class MermaidCliAdapter:
    """Render Mermaid source to an image using Mermaid CLI when available."""

    def __init__(
        self,
        cache_root: Path | None = None,
        cli_path: str | None | object = _AUTO_CLI,
    ) -> None:
        self.cache_root = cache_root or Path(tempfile.gettempdir()) / "mdscope-mermaid"
        if cli_path is _AUTO_CLI:
            self.cli_path = shutil.which("mmdc")
        else:
            self.cli_path = cast(str | None, cli_path)

    def is_available(self) -> bool:
        """Return whether Mermaid CLI is available."""
        return self.cli_path is not None

    def render_to_png(self, source: str) -> MermaidRenderResult:
        """Render Mermaid source to a cached PNG artifact."""
        if not self.is_available():
            return MermaidRenderResult(
                status="unavailable",
                message="Mermaid CLI no esta instalado. Instala `mmdc` para render real.",
            )

        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        self.cache_root.mkdir(parents=True, exist_ok=True)
        source_path = self.cache_root / f"{digest}.mmd"
        image_path = self.cache_root / f"{digest}.png"

        if image_path.exists():
            return MermaidRenderResult(status="rendered", image_path=image_path, cache_hit=True)

        source_path.write_text(source, encoding="utf-8")
        cli_path = self.cli_path
        if cli_path is None:
            return MermaidRenderResult(
                status="unavailable",
                message="Mermaid CLI no esta instalado. Instala `mmdc` para render real.",
            )
        completed = subprocess.run(
            [
                cli_path,
                "-i",
                str(source_path),
                "-o",
                str(image_path),
                "-b",
                "transparent",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )

        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "Mermaid CLI fallo."
            return MermaidRenderResult(status="error", message=message)

        if not image_path.exists():
            return MermaidRenderResult(
                status="error",
                message="Mermaid CLI termino sin generar el archivo PNG esperado.",
            )

        return MermaidRenderResult(status="rendered", image_path=image_path, cache_hit=False)
