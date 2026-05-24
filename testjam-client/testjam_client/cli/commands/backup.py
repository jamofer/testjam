"""`testjam backup` — download a full-instance backup archive."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="backup",
        help="Download full instance backup (admin only).",
        no_args_is_help=False,
        invoke_without_command=True,
    )
    app.callback(invoke_without_command=True)(download_backup)
    return app


def download_backup(
    context: typer.Context,
    out: Path | None = typer.Option(
        None, "--out", "-o",
        help="File or directory to write the archive into. Defaults to the current directory.",
    ),
) -> None:
    if context.invoked_subcommand is not None:
        return
    state: CliState = context.obj
    target = out if out is not None else Path.cwd()
    with output.progress("Requesting backup…", enabled=not state.json_output):
        with runtime.build_client(state) as client:
            written = client.backup.download(_resolve_destination(target))
    payload = {"path": str(written), "bytes": written.stat().st_size}
    output.render(payload, columns=["path", "bytes"], json_mode=state.json_output)


def _resolve_destination(target: Path) -> Path:
    if target.exists() and target.is_dir():
        return target
    if str(target).endswith(("/", "\\")):
        target.mkdir(parents=True, exist_ok=True)
        return target
    if target.suffix == "":
        # Bare name with no extension — treat as directory.
        target.mkdir(parents=True, exist_ok=True)
        return target
    return target


def _default_filename() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"testjam-backup-{stamp}.zip"
