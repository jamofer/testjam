"""`testjam run start|tail` — kick off and follow test executions."""
from __future__ import annotations

import json
import time
from typing import Any

import typer
from rich.live import Live
from rich.table import Table

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState


SHOW_COLUMNS = [
    "id", "title", "type", "status", "project_id", "plan_id",
    "version_id", "environment_id", "created_at",
]

DEFAULT_POLL_SECONDS = 1.0
TERMINAL_STATUSES = frozenset({"completed", "aborted"})
FAILED_RESULT_STATUSES = frozenset({"failed", "blocked"})
ABORTED_STATUS = "aborted"
EXIT_FAILED = 1
EXIT_ABORTED = 2


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="run",
        help="Start and follow test executions.",
        no_args_is_help=True,
    )
    app.command("start", help="Create + start a new test execution.")(start_run)
    app.command("tail", help="Poll an execution until it finishes (exit code = outcome).")(tail_run)
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
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def tail_run(
    context: typer.Context,
    execution_id: int = typer.Argument(..., help="Execution numeric id."),
    interval: float = typer.Option(
        DEFAULT_POLL_SECONDS, "--interval", help="Seconds between polls.",
    ),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        snapshot = _poll_until_terminal(client, execution_id, interval, state)
    if state.json_output:
        typer.echo(json.dumps(snapshot, indent=2, default=str))
    raise typer.Exit(_exit_code(snapshot["execution"], snapshot["results"]))


def _poll_until_terminal(
    client, execution_id: int, interval: float, state: CliState,
) -> dict[str, Any]:
    if state.json_output:
        return _poll_silent(client, execution_id, interval)
    return _poll_live(client, execution_id, interval)


def _poll_silent(client, execution_id: int, interval: float) -> dict[str, Any]:
    while True:
        snapshot = _take_snapshot(client, execution_id)
        if snapshot["execution"]["status"] in TERMINAL_STATUSES:
            return snapshot
        time.sleep(interval)


def _poll_live(client, execution_id: int, interval: float) -> dict[str, Any]:
    with Live(console=output.console, refresh_per_second=4, transient=False) as live:
        while True:
            snapshot = _take_snapshot(client, execution_id)
            live.update(_render_table(snapshot))
            if snapshot["execution"]["status"] in TERMINAL_STATUSES:
                return snapshot
            time.sleep(interval)


def _take_snapshot(client, execution_id: int) -> dict[str, Any]:
    return {
        "execution": client.executions.get(execution_id),
        "results": client.executions.list_results(execution_id),
    }


def _render_table(snapshot: dict[str, Any]) -> Table:
    execution = snapshot["execution"]
    table = Table(
        title=f"{execution.get('title', '')} — {execution.get('status', '')}",
        show_header=True, header_style="bold",
    )
    table.add_column("case_id")
    table.add_column("title")
    table.add_column("status")
    table.add_column("steps")
    table.add_column("duration_ms")
    for result in snapshot["results"]:
        steps = result.get("step_results") or []
        passed = sum(1 for step in steps if step.get("status") == "passed")
        table.add_row(
            str(result.get("test_case_id", "")),
            str(result.get("test_case_title") or ""),
            str(result.get("status") or ""),
            f"{passed}/{len(steps)}" if steps else "",
            str(result.get("duration_ms") or ""),
        )
    return table


def _exit_code(execution: dict, results: list[dict]) -> int:
    if execution.get("status") == ABORTED_STATUS:
        return EXIT_ABORTED
    if any(result.get("status") in FAILED_RESULT_STATUSES for result in results):
        return EXIT_FAILED
    return 0


def _parse_case_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(part) for part in raw.split(",") if part.strip()]
