"""`testjam bug list|show`."""
from __future__ import annotations

import typer

from testjam_client.cli import runtime
from testjam_client.cli.output import render
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "number", "title", "status", "severity", "assigned_to_id"]
SHOW_COLUMNS = [
    "id", "number", "title", "description", "status", "severity",
    "tags", "version_id", "fixed_in_version_id", "environment_id",
    "assigned_to_id", "reporter_id", "external_ticket_url", "created_at",
]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="bug",
        help="Inspect bugs.",
        no_args_is_help=True,
    )
    app.command("list", help="List bugs under a project.")(list_bugs)
    app.command("show", help="Show one bug by id or #number.")(show_bug)
    return app


def list_bugs(
    context: typer.Context,
    project: str | None = typer.Option(None, "--project", help="Override the active project."),
    status: str | None = typer.Option(None, "--status", help="Filter by status (open, in_progress, …)."),
    severity: str | None = typer.Option(None, "--severity", help="Filter by severity."),
    tag: str | None = typer.Option(None, "--tag", help="Filter by tag."),
    search: str | None = typer.Option(None, "--search", help="Search in title/description."),
    limit: int = typer.Option(50, "--limit", help="Maximum rows to fetch."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, project)
        rows = client.bugs.list(
            project_id,
            status=status,
            severity=severity,
            tag=tag,
            search=search,
            limit=limit,
        )
    render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_bug(
    context: typer.Context,
    reference: str = typer.Argument(..., help="Bug id, or '#N' for project-local number."),
    project: str | None = typer.Option(None, "--project", help="Required when using '#N'."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = _fetch_bug(client, state, reference, project)
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def _fetch_bug(client, state: CliState, reference: str, project: str | None) -> dict:
    if reference.startswith("#"):
        project_id = runtime.resolve_project_id(client, state, project)
        return client.bugs.get_by_number(project_id, int(reference[1:]))
    return client.bugs.get(int(reference))
