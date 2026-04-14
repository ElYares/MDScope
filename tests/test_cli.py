from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

import mdscope.cli.app as cli_app
from mdscope.ui.app import MDScopeApp


def test_help_shows_application_name() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_app.app, ["--help"])

    assert result.exit_code == 0
    assert "MDScope" in result.stdout


def test_main_uses_current_directory_by_default(monkeypatch: Any) -> None:
    runner = CliRunner()
    captured: dict[str, Path] = {}

    def fake_run(self: Any) -> None:
        captured["target"] = self.initial_target

    monkeypatch.setattr(MDScopeApp, "run", fake_run)

    result = runner.invoke(cli_app.app, [])

    assert result.exit_code == 0
    assert result.stdout == ""
    assert captured["target"] == Path.cwd().resolve()


def test_main_fails_when_target_does_not_exist() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_app.app, ["missing.md"])

    assert result.exit_code == 2
    assert "Target no existe:" in result.stderr
