"""`testjam run start|tail` — kick off and follow test executions."""
from __future__ import annotations

import json
import time
from typing import Any

import httpx
import typer
from rich.live import Live
from rich.table import Table

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState
from testjam_client.errors import RateLimited, ServerError


SHOW_COLUMNS = [
    "id", "title", "type", "status", "project_id",
    "version_id", "environment", "created_at",
]

DEFAULT_POLL_SECONDS = 1.0
TERMINAL_STATUSES = frozenset({"completed", "aborted"})
FAILED_RESULT_STATUSES = frozenset({"failed", "blocked"})
ABORTED_STATUS = "aborted"
EXIT_FAILED = 1
EXIT_ABORTED = 2
EXIT_TIMED_OUT = 3
EXIT_UNREACHABLE = 4
UNREACHABLE_GIVE_UP_SECONDS = 300.0
TRANSIENT_ERRORS = (httpx.TransportError, ServerError, RateLimited)


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
            test_case_ids = list(plan.get("test_case_ids") or [])
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
    timeout: float = typer.Option(
        0, "--timeout", help="Give up after this many seconds (exit 3). 0 waits forever.",
    ),
) -> None:
    state: CliState = context.obj
    try:
        with runtime.build_client(state) as client:
            snapshot = _poll_until_terminal(client, execution_id, interval, timeout, state)
    except TailStopped as stop:
        typer.echo(str(stop), err=True)
        raise typer.Exit(stop.exit_code) from stop
    if state.json_output:
        typer.echo(json.dumps(snapshot, indent=2, default=str))
    raise typer.Exit(_exit_code(snapshot["execution"], snapshot["results"]))


class TailStopped(Exception):
    """Polling ended before the execution finished."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _poll_until_terminal(
    client, execution_id: int, interval: float, timeout: float, state: CliState,
) -> dict[str, Any]:
    snapshots = _snapshots(client, execution_id, interval, timeout)
    if state.json_output:
        return _last(snapshots)
    with Live(console=output.console, refresh_per_second=4, transient=False) as live:
        return _last(snapshots, on_snapshot=lambda snapshot: live.update(_render_table(snapshot)))


def _last(snapshots, on_snapshot=lambda _snapshot: None) -> dict[str, Any]:
    snapshot = None
    for snapshot in snapshots:
        on_snapshot(snapshot)
    return snapshot


def _snapshots(client, execution_id: int, interval: float, timeout: float):
    """Yield snapshots until the execution finishes, riding out transient failures."""
    started = last_reached = time.monotonic()
    while True:
        try:
            snapshot = _take_snapshot(client, execution_id)
        except TRANSIENT_ERRORS as exc:
            if time.monotonic() - last_reached > UNREACHABLE_GIVE_UP_SECONDS:
                raise TailStopped(EXIT_UNREACHABLE, f"Server unreachable, giving up: {exc}") from exc
        else:
            last_reached = time.monotonic()
            yield snapshot
            if snapshot["execution"]["status"] in TERMINAL_STATUSES:
                return
        if timeout and time.monotonic() - started >= timeout:
            raise TailStopped(EXIT_TIMED_OUT, f"Execution {execution_id} still running after {timeout:g}s")
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
