from __future__ import annotations

from mdscope.adapters.plotext_adapter import PlotextAdapter, parse_chart_block


def test_parse_chart_block_parses_line_spec() -> None:
    spec = parse_chart_block(
        "\n".join(
            [
                "title: Requests",
                "type: line",
                "x: 1,2,3",
                "y: 12,18,9",
                "xlabel: Dia",
                "ylabel: Total",
            ]
        )
    )

    assert spec.chart_type == "line"
    assert spec.title == "Requests"
    assert spec.x_values == ("1", "2", "3")
    assert spec.y_values == (12.0, 18.0, 9.0)
    assert spec.x_label == "Dia"
    assert spec.y_label == "Total"


def test_parse_chart_block_rejects_invalid_type() -> None:
    try:
        parse_chart_block("type: area\ny: 1,2,3")
    except ValueError as exc:
        assert "line" in str(exc)
    else:
        assert False, "expected ValueError"


def test_plotext_adapter_reports_unavailable_when_plotext_missing() -> None:
    adapter = PlotextAdapter()
    adapter.is_available = lambda: False  # type: ignore[method-assign]

    result = adapter.render("type: line\ny: 1,2,3")

    assert result.status == "unavailable"
