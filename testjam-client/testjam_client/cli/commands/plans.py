"""`testjam plan list|show`."""
from __future__ import annotations

import typer

from testjam_client.cli import runtime
from testjam_client.cli.output import render
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "title", "description", "case_count"]
SHOW_COLUMNS = ["id", "title", "description", "project_id", "case_ids"]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="plan",
        help="Inspect test plans.",
        no_args_is_help=True,
    )
    app.command("list", help="List plans under a project.")(list_plans)
    app.command("show", help="Show one plan by id.")(show_plan)
    app.command("create", help="Create a new test plan.")(create_plan)
    return app


def list_plans(
    context: typer.Context,
    project: str | None = typer.Option(None, "--project", help="Override the active project."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, project)
        rows = client.plans.list(project_id)
    render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_plan(
    context: typer.Context,
    plan_id: int = typer.Argument(..., help="Plan numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = client.plans.get(plan_id)
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def create_plan(
    context: typer.Context,
    title: str = typer.Argument(..., help="Plan title."),
    project: str | None = typer.Option(None, "--project"),
    description: str | None = typer.Option(None, "--description"),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, project)
        payload = client.plans.create(project_id, title, description=description)
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)
