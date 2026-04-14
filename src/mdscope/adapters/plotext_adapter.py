"""Adapter for terminal charts rendered with plotext."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from importlib.util import find_spec


@dataclass(frozen=True)
class ChartSpec:
    """Parsed chart specification from a Markdown fence."""

    chart_type: str
    title: str | None
    x_values: tuple[str, ...]
    y_values: tuple[float, ...]
    x_label: str | None = None
    y_label: str | None = None


@dataclass(frozen=True)
class ChartRenderResult:
    """Result of attempting to render a chart block."""

    status: str
    output: str | None = None
    message: str | None = None


class PlotextAdapter:
    """Render simple chart specs to terminal output using plotext."""

    def __init__(self, python_executable: str | None = None) -> None:
        self.python_executable = python_executable or sys.executable

    def is_available(self) -> bool:
        """Return whether plotext is installed in the current environment."""
        return find_spec("plotext") is not None

    def render(self, chart_source: str, *, width: int = 72, height: int = 18) -> ChartRenderResult:
        """Render a chart block to ANSI terminal output."""
        try:
            spec = parse_chart_block(chart_source)
        except ValueError as exc:
            return ChartRenderResult(status="invalid", message=str(exc))

        if not self.is_available():
            return ChartRenderResult(
                status="unavailable",
                message=(
                    "plotext no esta instalado. "
                    "Usa las dependencias de charts para render real."
                ),
            )

        payload = {
            "type": spec.chart_type,
            "title": spec.title,
            "x": list(spec.x_values),
            "y": list(spec.y_values),
            "xlabel": spec.x_label,
            "ylabel": spec.y_label,
            "width": width,
            "height": height,
        }

        completed = subprocess.run(
            [self.python_executable, "-c", _PLOTEXT_RENDER_SCRIPT],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "plotext fallo."
            return ChartRenderResult(status="error", message=message)

        output = completed.stdout.rstrip()
        if not output:
            return ChartRenderResult(status="error", message="plotext no produjo salida.")

        return ChartRenderResult(status="rendered", output=output)


def parse_chart_block(chart_source: str) -> ChartSpec:
    """Parse the supported chart block format."""
    values: dict[str, str] = {}
    for raw_line in chart_source.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(
                "Formato de chart invalido. Usa lineas tipo `clave: valor`."
            )
        key, value = line.split(":", maxsplit=1)
        values[key.strip().lower()] = value.strip()

    chart_type = values.get("type", "line").lower()
    if chart_type not in {"line", "bar"}:
        raise ValueError("Tipo de chart no soportado. Usa `line` o `bar`.")

    y_raw = values.get("y")
    if not y_raw:
        raise ValueError("El bloque chart requiere `y:` con valores numericos.")
    y_values = tuple(_parse_numeric_list(y_raw))

    x_raw = values.get("x")
    if x_raw:
        x_values = tuple(_parse_string_list(x_raw))
    else:
        x_values = tuple(str(index + 1) for index in range(len(y_values)))

    if len(x_values) != len(y_values):
        raise ValueError("Las listas `x` y `y` deben tener la misma longitud.")

    return ChartSpec(
        chart_type=chart_type,
        title=values.get("title") or None,
        x_values=x_values,
        y_values=y_values,
        x_label=values.get("xlabel") or None,
        y_label=values.get("ylabel") or None,
    )


def _parse_string_list(raw_values: str) -> list[str]:
    items = [item.strip() for item in raw_values.split(",")]
    return [item for item in items if item]


def _parse_numeric_list(raw_values: str) -> list[float]:
    numbers: list[float] = []
    for item in _parse_string_list(raw_values):
        try:
            numbers.append(float(item))
        except ValueError as exc:
            raise ValueError(f"Valor numerico invalido en `y`: {item}") from exc
    return numbers


_PLOTEXT_RENDER_SCRIPT = """
import json
import sys

import plotext as plt

payload = json.load(sys.stdin)
x_values = payload["x"]
y_values = payload["y"]
chart_type = payload["type"]

def _as_numeric(values):
    converted = []
    for value in values:
        try:
            converted.append(float(value))
        except ValueError:
            return None
    return converted

plt.clf()
plt.plotsize(payload["width"], payload["height"])
if payload.get("title"):
    plt.title(payload["title"])
if payload.get("xlabel"):
    plt.xlabel(payload["xlabel"])
if payload.get("ylabel"):
    plt.ylabel(payload["ylabel"])

numeric_x = _as_numeric(x_values)

if chart_type == "line":
    if numeric_x is None:
        plt.plot(y_values)
    else:
        plt.plot(numeric_x, y_values)
else:
    if numeric_x is None:
        plt.bar(x_values, y_values)
    else:
        plt.bar(numeric_x, y_values)

plt.show()
"""
