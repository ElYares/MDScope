"""Terminal capability detection."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class TerminalCapabilities:
    """Capabilities relevant to optional rich rendering."""

    kitty_graphics: bool
    chafa_available: bool


def detect_terminal_capabilities() -> TerminalCapabilities:
    """Detect optional terminal/image capabilities."""
    term = os.environ.get("TERM", "")
    term_program = os.environ.get("TERM_PROGRAM", "")
    kitty_graphics = "kitty" in term.lower() or "kitty" in term_program.lower()
    chafa_available = shutil.which("chafa") is not None
    return TerminalCapabilities(
        kitty_graphics=kitty_graphics,
        chafa_available=chafa_available,
    )
