"""Renderable helpers for table and matrix blocks."""

from __future__ import annotations

import csv
from io import StringIO

from rich.box import SIMPLE_HEAVY
from rich.panel import Panel
from rich.table import Table


def render_table_block(table_source: str) -> Table | Panel:
    """Render a pipe- or tab-delimited table block."""
    rows = _parse_delimited_rows(table_source)
    if len(rows) < 2:
        return Panel.fit(
            "Bloque table invalido. Incluye header y al menos una fila.",
            title="Table",
            border_style="red",
        )
    header, *body = rows
    return _build_rich_table(header, body, title="Tabla")


def render_matrix_block(matrix_source: str) -> Table | Panel:
    """Render a simple matrix block using commas, pipes or tabs."""
    rows = _parse_delimited_rows(matrix_source, default_delimiter=",")
    if not rows:
        return Panel.fit(
            "Bloque matrix invalido. Incluye al menos una fila.",
            title="Matrix",
            border_style="red",
        )
    width = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]
    header = [f"C{index + 1}" for index in range(width)]
    return _build_rich_table(header, normalized_rows, title="Matrix", show_header=False)


def _parse_delimited_rows(source: str, default_delimiter: str = "|") -> list[list[str]]:
    lines = [line.strip() for line in source.strip().splitlines() if line.strip()]
    if not lines:
        return []
    delimiter = _detect_delimiter(lines, default_delimiter)
    rows = [_split_row(line, delimiter) for line in lines]
    return [row for row in rows if any(cell for cell in row)]


def _detect_delimiter(lines: list[str], default_delimiter: str) -> str:
    for delimiter in ("|", "\t", ";", ","):
        if any(delimiter in line for line in lines):
            return delimiter
    return default_delimiter


def _split_row(line: str, delimiter: str) -> list[str]:
    if delimiter == "|":
        stripped = line.strip("|")
        cells = [cell.strip() for cell in stripped.split("|")]
        return [cell for cell in cells]
    reader = csv.reader(StringIO(line), delimiter=delimiter)
    return [cell.strip() for cell in next(reader)]


def _build_rich_table(
    header: list[str],
    rows: list[list[str]],
    *,
    title: str,
    show_header: bool = True,
) -> Table:
    table = Table(
        title=title,
        box=SIMPLE_HEAVY,
        show_header=show_header,
        header_style="bold cyan",
        expand=True,
    )
    for column_name in header:
        style = "bold cyan" if show_header else "white"
        table.add_column(column_name or " ", overflow="fold", ratio=1, style=style)
    for row in rows:
        normalized_row = row + [""] * (len(header) - len(row))
        table.add_row(*normalized_row[: len(header)])
    return table
