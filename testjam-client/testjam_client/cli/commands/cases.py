"""`testjam case list|show|create`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "name", "external_id", "is_archived"]
SHOW_COLUMNS = ["id", "name", "description", "external_id", "suite_id", "is_archived"]
STEP_SEPARATOR = " => "


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="case",
        help="Inspect and create test cases.",
        no_args_is_help=True,
    )
    app.command("list", help="List cases under a suite.")(list_cases)
    app.command("show", help="Show one case by id.")(show_case)
    app.command("create", help="Create a test case (optionally with steps).")(create_case)
    return app


def list_cases(
    context: typer.Context,
    suite_id: int = typer.Option(..., "--suite", help="Suite numeric id."),
    include_archived: bool = typer.Option(False, "--archived", help="Include archived cases."),
) -> None:
    state: CliState = context.obj
    with output.progress("Loading cases…", enabled=not state.json_output):
        with runtime.build_client(state) as client:
            rows = client.cases.list(suite_id, include_archived=include_archived)
    output.render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_case(
    context: typer.Context,
    case_id: int = typer.Argument(..., help="Case numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = client.cases.get(case_id)
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def create_case(
    context: typer.Context,
    name: str = typer.Argument(..., help="Case name."),
    suite_id: int = typer.Option(..., "--suite", help="Suite numeric id."),
    description: str | None = typer.Option(None, "--description"),
    external_id: str | None = typer.Option(None, "--external-id"),
    steps_source: str | None = typer.Option(
        None,
        "--steps",
        help="Path to a steps file, or '-' for stdin. Lines or JSON.",
    ),
) -> None:
    state: CliState = context.obj
    steps = _load_steps(steps_source)

    with runtime.build_client(state) as client:
        payload = client.cases.create(
            suite_id, name, description=description, external_id=external_id,
        )
        if steps:
            client.cases.replace_steps(payload["id"], steps)
            payload = client.cases.get(payload["id"])
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def _load_steps(source: str | None) -> list[dict]:
    if source is None:
        return []
    content = sys.stdin.read() if source == "-" else Path(source).read_text()
    return _parse_steps(content)


def _parse_steps(content: str) -> list[dict]:
    stripped = content.strip()
    if not stripped:
        return []
    if stripped[0] in "[{":
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, list) else [parsed]
    return [_line_to_step(line) for line in stripped.splitlines() if line.strip()]


def _line_to_step(line: str) -> dict:
    if STEP_SEPARATOR in line:
        action, expected = line.split(STEP_SEPARATOR, 1)
        return {"action": action.strip(), "expected_result": expected.strip()}
    return {"action": line.strip()}
