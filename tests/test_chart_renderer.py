from __future__ import annotations

from dataclasses import dataclass

from rich.panel import Panel

from mdscope.adapters.plotext_adapter import ChartRenderResult
from mdscope.renderers.chart_renderer import render_chart_block


@dataclass
class FakeChartAdapter:
    result: ChartRenderResult

    def render(self, chart_source: str, *, width: int = 72, height: int = 18) -> ChartRenderResult:
        return self.result


def test_render_chart_block_returns_rendered_panel() -> None:
    renderable = render_chart_block(
        "type: line\ny: 1,2,3",
        adapter=FakeChartAdapter(ChartRenderResult(status="rendered", output="chart")),
    )

    assert isinstance(renderable, Panel)


def test_render_chart_block_returns_invalid_panel() -> None:
    renderable = render_chart_block(
        "type: line\ny: a,b,c",
        adapter=FakeChartAdapter(ChartRenderResult(status="invalid", message="bad y")),
    )

    assert isinstance(renderable, Panel)
