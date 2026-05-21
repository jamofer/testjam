"""Build a `TestjamClient` from the active CLI state and resolve project refs."""
from __future__ import annotations

import typer

from testjam_client import TestjamClient
from testjam_client.cli.state import CliState


def build_client(state: CliState) -> TestjamClient:
    profile = state.profile
    url = profile.get("url")
    if not url:
        raise typer.BadParameter(
            "No server URL in this profile. "
            "Run `testjam login --url ...` or `testjam config set url ...`."
        )
    token = profile.get("token")
    api_key = state.api_key_override or profile.get("api_key")
    return TestjamClient(url, token=token, api_key=api_key)


def resolve_project_id(
    client: TestjamClient,
    state: CliState,
    explicit: str | None,
) -> int:
    raw = explicit or state.project_override or state.profile.get("default_project")
    if not raw:
        raise typer.BadParameter(
            "No project — pass --project NAME_OR_ID or "
            "`testjam config set default_project ...`."
        )
    if raw.isdigit():
        return int(raw)
    project = client.projects.find_by_name(raw)
    if not project:
        raise typer.BadParameter(f"Project '{raw}' not found.")
    return project["id"]
