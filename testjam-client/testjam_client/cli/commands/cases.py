"""`testjam case list|show`."""
from __future__ import annotations

import typer

from testjam_client.cli import runtime
from testjam_client.cli.output import render
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "name", "external_id", "is_archived"]
SHOW_COLUMNS = ["id", "name", "description", "external_id", "suite_id", "is_archived"]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="case",
        help="Inspect test cases.",
        no_args_is_help=True,
    )
    app.command("list", help="List cases under a suite.")(list_cases)
    app.command("show", help="Show one case by id.")(show_case)
    return app


def list_cases(
    context: typer.Context,
    suite_id: int = typer.Option(..., "--suite", help="Suite numeric id."),
    include_archived: bool = typer.Option(False, "--archived", help="Include archived cases."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        rows = client.cases.list(suite_id, include_archived=include_archived)
    render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_case(
    context: typer.Context,
    case_id: int = typer.Argument(..., help="Case numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = client.cases.get(case_id)
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)
