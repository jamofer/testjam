"""`testjam about` — show client + server build metadata."""
from __future__ import annotations

from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version

import httpx
import typer

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState


PACKAGE_NAME = "testjam-client"
UNKNOWN = "unknown"


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="about",
        help="Show client + server build metadata.",
        no_args_is_help=False,
        invoke_without_command=True,
    )
    app.callback(invoke_without_command=True)(show_about)
    return app


def show_about(context: typer.Context) -> None:
    if context.invoked_subcommand is not None:
        return
    state: CliState = context.obj
    payload = {
        "client_version": _client_version(),
        "server_url": state.profile.get("url"),
        "server_version": UNKNOWN,
        "server_ref": UNKNOWN,
        "server_commit": UNKNOWN,
        "server_built_at": UNKNOWN,
        "server_status": "unreachable",
    }
    server = _fetch_server(state)
    if server is not None:
        payload.update({
            "server_version": server["version"],
            "server_ref": server["ref"],
            "server_commit": server["commit"],
            "server_built_at": server["built_at"],
            "server_status": "ok",
        })
    columns = [
        "client_version",
        "server_url",
        "server_status",
        "server_version",
        "server_ref",
        "server_commit",
        "server_built_at",
    ]
    output.render(payload, columns=columns, json_mode=state.json_output)


def _fetch_server(state: CliState) -> dict | None:
    try:
        with runtime.build_client(state) as client:
            return asdict(client.about.get())
    except (httpx.HTTPError, typer.BadParameter):
        return None


def _client_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return UNKNOWN
