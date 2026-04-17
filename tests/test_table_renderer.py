from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from mdscope.renderers.table_renderer import render_matrix_block, render_table_block


def test_render_table_block_returns_table_for_valid_input() -> None:
    renderable = render_table_block("Metodo|Formula\nMifflin|10xkg")

    assert isinstance(renderable, Table)


def test_render_table_block_returns_panel_for_invalid_input() -> None:
    renderable = render_table_block("Solo una fila")

    assert isinstance(renderable, Panel)


def test_render_matrix_block_returns_table() -> None:
    renderable = render_matrix_block("1,2\n3,4")

    assert isinstance(renderable, Table)
