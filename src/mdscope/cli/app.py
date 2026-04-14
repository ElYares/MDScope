"""CLI entrypoint for MDScope."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from mdscope.ui.app import MDScopeApp

app = typer.Typer(
    name="mdscope",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=False,
    help="MDScope: lector TUI de documentacion tecnica en Markdown.",
)


def _normalize_target(target: str | None) -> Path:
    """Resolve the requested path or default to the current directory."""
    if target is None:
        return Path.cwd().resolve()
    return Path(target).expanduser().resolve()


@app.command()
def main(
    target: Annotated[
        str | None,
        typer.Argument(
            help="Archivo Markdown o directorio de documentacion.",
        ),
    ] = None,
) -> None:
    """Open MDScope with a file or project path."""
    resolved_target = _normalize_target(target)
    if not resolved_target.exists():
        typer.echo(f"Target no existe: {resolved_target}", err=True)
        raise typer.Exit(code=2)

    MDScopeApp(initial_target=resolved_target).run()


def run() -> None:
    """Execute the Typer application."""
    app()


if __name__ == "__main__":
    run()
