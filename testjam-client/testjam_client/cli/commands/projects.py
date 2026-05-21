"""`testjam project list|show`."""
from __future__ import annotations

import typer

from testjam_client.cli import runtime
from testjam_client.cli.output import render
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "name", "description", "is_active"]
SHOW_COLUMNS = ["id", "name", "description", "is_active", "created_at"]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="project",
        help="Inspect projects.",
        no_args_is_help=True,
    )
    app.command("list", help="List projects visible to the current user.")(list_projects)
    app.command("show", help="Show one project by name or id.")(show_project)
    return app


def list_projects(context: typer.Context) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        rows = client.projects.list()
    render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_project(
    context: typer.Context,
    name_or_id: str = typer.Argument(..., help="Project name or numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, name_or_id)
        payload = client.projects.get(project_id)
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)
