"""Renderable helpers for math blocks and inline formulas."""

from __future__ import annotations

import re

from rich.panel import Panel
from rich.text import Text

_LATEX_COMMAND_REPLACEMENTS = {
    r"\times": "×",
    r"\cdot": "·",
    r"\pm": "±",
    r"\mp": "∓",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\neq": "≠",
    r"\approx": "≈",
    r"\to": "→",
    r"\rightarrow": "→",
    r"\leftarrow": "←",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\mu": "μ",
}


def render_math_block(math_source: str) -> Panel:
    """Render a LaTeX-like math block into a terminal-friendly panel."""
    normalized = convert_latex_to_terminal(math_source)
    return Panel.fit(
        Text(normalized, style="bold bright_white"),
        title="Formula",
        border_style="magenta",
    )


def replace_inline_math(markdown_text: str) -> str:
    """Replace inline and block LaTeX delimiters with terminal-friendly text."""
    markdown_text = re.sub(
        r"\$\$(?P<body>.*?)\$\$",
        lambda match: "\n" + convert_latex_to_terminal(match.group("body")) + "\n",
        markdown_text,
        flags=re.DOTALL,
    )
    return re.sub(
        r"(?<!\\)\$(?P<body>[^$\n]+?)(?<!\\)\$",
        lambda match: convert_latex_to_terminal(match.group("body")),
        markdown_text,
    )


def convert_latex_to_terminal(latex_source: str) -> str:
    """Convert a limited subset of LaTeX notation into readable terminal text."""
    normalized = latex_source.strip()
    for latex_command, replacement in _LATEX_COMMAND_REPLACEMENTS.items():
        normalized = normalized.replace(latex_command, replacement)
    normalized = re.sub(
        r"\\frac\{(?P<num>[^{}]+)\}\{(?P<den>[^{}]+)\}",
        lambda match: f"({match.group('num')})/({match.group('den')})",
        normalized,
    )
    normalized = re.sub(
        r"(?P<base>[A-Za-z0-9]+)_\{(?P<sub>[^{}]+)\}",
        lambda match: f"{match.group('base')}_{match.group('sub')}",
        normalized,
    )
    normalized = re.sub(
        r"(?P<base>[A-Za-z0-9]+)\^\{(?P<sup>[^{}]+)\}",
        lambda match: f"{match.group('base')}^{match.group('sup')}",
        normalized,
    )
    normalized = normalized.replace(r"\_", "_")
    normalized = normalized.replace("{", "").replace("}", "")
    normalized = re.sub(r"\\[A-Za-z]+", "", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()
