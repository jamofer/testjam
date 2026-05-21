"""Testjam command-line client entry point."""
from importlib.metadata import PackageNotFoundError, version

import typer

PACKAGE_NAME = "testjam-client"
FALLBACK_VERSION = "0.0.0"

app = typer.Typer(
    name="testjam",
    help="Testjam command-line client.",
    no_args_is_help=True,
)


def main() -> None:
    app()


def _resolve_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return FALLBACK_VERSION


def _version_callback(value: bool) -> None:
    if not value:
        return
    typer.echo(f"testjam {_resolve_version()}")
    raise typer.Exit()


@app.callback()
def root(
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the testjam CLI version and exit.",
    ),
) -> None:
    """Testjam command-line client."""
