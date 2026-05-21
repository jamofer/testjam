"""`testjam execution list|show`."""
from __future__ import annotations

import typer

from testjam_client.cli import runtime
from testjam_client.cli.output import render
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "title", "type", "status", "created_at"]
SHOW_COLUMNS = [
    "id", "title", "type", "status", "project_id", "version_id",
    "environment_id", "plan_id", "created_at", "completed_at",
]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="execution",
        help="Inspect test executions (manual and automatic).",
        no_args_is_help=True,
    )
    app.command("list", help="List executions under a project.")(list_executions)
    app.command("show", help="Show one execution by id.")(show_execution)
    return app


def list_executions(
    context: typer.Context,
    project: str | None = typer.Option(None, "--project", help="Override the active project."),
    status: str | None = typer.Option(None, "--status", help="Filter: pending|in_progress|completed|aborted."),
    execution_type: str | None = typer.Option(None, "--type", help="Filter: manual|automatic."),
    limit: int = typer.Option(50, "--limit", help="Maximum rows to fetch."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, project)
        rows = client.executions.list(
            project_id, type=execution_type, status=status, limit=limit,
        )
    render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_execution(
    context: typer.Context,
    execution_id: int = typer.Argument(..., help="Execution numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = client.executions.get(execution_id)
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)
