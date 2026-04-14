"""Helpers for rendering code blocks."""

from __future__ import annotations

from rich.syntax import Syntax


def render_code_block(code: str, language: str | None) -> Syntax:
    """Render a fenced code block with syntax highlighting."""
    lexer = language or "text"
    return Syntax(code.rstrip("\n"), lexer=lexer, theme="monokai", line_numbers=False)
