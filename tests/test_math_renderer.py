from __future__ import annotations

from rich.panel import Panel

from mdscope.renderers.math_renderer import convert_latex_to_terminal, render_math_block


def test_convert_latex_to_terminal_replaces_common_math_tokens() -> None:
    rendered = convert_latex_to_terminal(r"REE = 10 \times peso_{kg} + \frac{6.25}{2}")

    assert "×" in rendered
    assert "peso_kg" in rendered
    assert "(6.25)/(2)" in rendered


def test_render_math_block_returns_panel() -> None:
    renderable = render_math_block(r"REE = 10 \times peso_{kg}")

    assert isinstance(renderable, Panel)
