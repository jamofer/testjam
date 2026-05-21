"""`testjam suite list|show`."""
from __future__ import annotations

import typer

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "name", "parent_suite_id", "case_count"]
SHOW_COLUMNS = ["id", "name", "description", "parent_suite_id", "project_id"]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="suite",
        help="Inspect test suites.",
        no_args_is_help=True,
    )
    app.command("list", help="List suites under a project.")(list_suites)
    app.command("show", help="Show one suite by id.")(show_suite)
    return app


def list_suites(
    context: typer.Context,
    project: str | None = typer.Option(None, "--project", help="Override the active project."),
    include_all: bool = typer.Option(False, "--all", help="Include nested suites, not only top-level."),
) -> None:
    state: CliState = context.obj
    with output.progress("Loading suites…", enabled=not state.json_output):
        with runtime.build_client(state) as client:
            project_id = runtime.resolve_project_id(client, state, project)
            rows = client.suites.list(project_id, all=include_all)
    output.render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_suite(
    context: typer.Context,
    suite_id: int = typer.Argument(..., help="Suite numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = client.suites.get(suite_id)
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)
