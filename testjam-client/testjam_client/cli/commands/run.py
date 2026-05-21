"""`testjam run start` (and, in the next phase, `run tail`)."""
from __future__ import annotations

import typer

from testjam_client.cli import runtime
from testjam_client.cli.output import render
from testjam_client.cli.state import CliState


SHOW_COLUMNS = [
    "id", "title", "type", "status", "project_id", "plan_id",
    "version_id", "environment_id", "created_at",
]


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="run",
        help="Start and follow test executions.",
        no_args_is_help=True,
    )
    app.command("start", help="Create + start a new test execution.")(start_run)
    return app


def start_run(
    context: typer.Context,
    title: str = typer.Argument(..., help="Execution title."),
    project: str | None = typer.Option(None, "--project"),
    plan_id: int | None = typer.Option(None, "--plan"),
    case_ids: str | None = typer.Option(
        None,
        "--cases",
        help="Comma-separated case ids (when --plan is not used).",
    ),
    execution_type: str = typer.Option("manual", "--type", help="manual|automatic"),
    version_id: int | None = typer.Option(None, "--version"),
    environment: str | None = typer.Option(None, "--environment"),
    assigned_to_id: int | None = typer.Option(None, "--assigned-to"),
) -> None:
    state: CliState = context.obj
    test_case_ids = _parse_case_ids(case_ids)

    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, project)
        runtime.confirm_or_abort(
            f"Start {execution_type} run '{title}' in project {project_id}?", state,
        )
        if plan_id is not None and not test_case_ids:
            plan = client.plans.get(plan_id)
            test_case_ids = list(plan.get("case_ids") or [])
        payload = client.executions.create(
            project_id,
            title=title,
            type=execution_type,
            test_case_ids=test_case_ids or None,
            version_id=version_id,
            environment=environment,
            assigned_to_id=assigned_to_id,
        )
    render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def _parse_case_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(part) for part in raw.split(",") if part.strip()]
