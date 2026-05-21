"""`testjam bug` — list/show/create/update/comment/status/watch/unwatch."""
from __future__ import annotations

import sys
from pathlib import Path

import typer

from testjam_client.cli import output, runtime
from testjam_client.cli.state import CliState


LIST_COLUMNS = ["id", "number", "title", "status", "severity", "assigned_to_id"]
SHOW_COLUMNS = [
    "id", "number", "title", "description", "status", "severity",
    "tags", "version_id", "fixed_in_version_id", "environment_id",
    "assigned_to_id", "reporter_id", "external_ticket_url", "created_at",
]
COMMENT_COLUMNS = ["id", "body", "user_id", "created_at"]
STDIN_MARKER = "-"


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="bug",
        help="Inspect and manage bugs.",
        no_args_is_help=True,
    )
    app.command("list", help="List bugs under a project.")(list_bugs)
    app.command("show", help="Show one bug by id or '#N'.")(show_bug)
    app.command("create", help="Create a new bug.")(create_bug)
    app.command("update", help="Update an existing bug.")(update_bug)
    app.command("watch", help="Subscribe to bug notifications.")(watch_bug)
    app.command("unwatch", help="Stop watching the bug.")(unwatch_bug)
    app.add_typer(_build_comment_app(), name="comment")
    app.add_typer(_build_status_app(), name="status")
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
    with output.progress("Loading bugs…", enabled=not state.json_output):
        with runtime.build_client(state) as client:
            project_id = runtime.resolve_project_id(client, state, project)
            rows = client.bugs.list(
                project_id,
                status=status, severity=severity, tag=tag, search=search, limit=limit,
            )
    output.render(rows, columns=LIST_COLUMNS, json_mode=state.json_output)


def show_bug(
    context: typer.Context,
    reference: str = typer.Argument(..., help="Bug id, or '#N' for project-local number."),
    project: str | None = typer.Option(None, "--project", help="Required when using '#N'."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        payload = _fetch_bug(client, state, reference, project)
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def create_bug(
    context: typer.Context,
    title: str = typer.Argument(..., help="Bug title."),
    project: str | None = typer.Option(None, "--project"),
    description: str | None = typer.Option(None, "--description"),
    severity: str = typer.Option("medium", "--severity"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags."),
    version_id: int | None = typer.Option(None, "--version"),
    fixed_in_version_id: int | None = typer.Option(None, "--fixed-in"),
    assigned_to_id: int | None = typer.Option(None, "--assigned-to"),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        project_id = runtime.resolve_project_id(client, state, project)
        payload = client.bugs.create(
            project_id,
            title=title,
            description=description,
            severity=severity,
            tags=_parse_tags(tags),
            version_id=version_id,
            fixed_in_version_id=fixed_in_version_id,
            assigned_to_id=assigned_to_id,
        )
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def update_bug(
    context: typer.Context,
    bug_id: int = typer.Argument(..., help="Bug numeric id."),
    title: str | None = typer.Option(None, "--title"),
    description: str | None = typer.Option(None, "--description"),
    severity: str | None = typer.Option(None, "--severity"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags. Use '' to clear."),
    assigned_to_id: int | None = typer.Option(None, "--assigned-to"),
    version_id: int | None = typer.Option(None, "--version"),
    fixed_in_version_id: int | None = typer.Option(None, "--fixed-in"),
) -> None:
    state: CliState = context.obj
    payload = _build_update_payload(
        title=title,
        description=description,
        severity=severity,
        tags=tags,
        assigned_to_id=assigned_to_id,
        version_id=version_id,
        fixed_in_version_id=fixed_in_version_id,
    )
    if not payload:
        typer.echo("Nothing to update — supply at least one --field.", err=True)
        raise typer.Exit(code=2)

    with runtime.build_client(state) as client:
        result = client.bugs.update(bug_id, **payload)
    output.render(result, columns=SHOW_COLUMNS, json_mode=state.json_output)


def watch_bug(
    context: typer.Context,
    bug_id: int = typer.Argument(..., help="Bug numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        client.bugs.watch(bug_id)
    typer.echo(f"Watching bug {bug_id}")


def unwatch_bug(
    context: typer.Context,
    bug_id: int = typer.Argument(..., help="Bug numeric id."),
) -> None:
    state: CliState = context.obj
    with runtime.build_client(state) as client:
        client.bugs.unwatch(bug_id)
    typer.echo(f"No longer watching bug {bug_id}")


def _build_comment_app() -> typer.Typer:
    app = typer.Typer(help="Comments on a bug.", no_args_is_help=True)
    app.command("add", help="Add a comment. Body from arg, --file, or '-' for stdin.")(add_comment)
    return app


def add_comment(
    context: typer.Context,
    bug_id: int = typer.Argument(..., help="Bug numeric id."),
    body: str | None = typer.Argument(None, help="Comment body, or '-' for stdin."),
    file: Path | None = typer.Option(None, "--file", help="Read body from a file."),
) -> None:
    state: CliState = context.obj
    text = _resolve_comment_body(body, file)
    with runtime.build_client(state) as client:
        payload = client.bugs.add_comment(bug_id, text)
    output.render(payload, columns=COMMENT_COLUMNS, json_mode=state.json_output)


def _build_status_app() -> typer.Typer:
    app = typer.Typer(help="Bug status transitions.", no_args_is_help=True)
    app.command("change", help="Change the bug status (notifies watchers).")(change_status)
    return app


def change_status(
    context: typer.Context,
    bug_id: int = typer.Argument(..., help="Bug numeric id."),
    new_status: str = typer.Argument(..., help="Target status."),
    note: str | None = typer.Option(None, "--note", help="Optional transition note."),
) -> None:
    state: CliState = context.obj
    runtime.confirm_or_abort(
        f"Change bug {bug_id} status to '{new_status}'?", state,
    )
    with runtime.build_client(state) as client:
        payload = client.bugs.change_status(bug_id, new_status, note=note)
    output.render(payload, columns=SHOW_COLUMNS, json_mode=state.json_output)


def _fetch_bug(client, state: CliState, reference: str, project: str | None) -> dict:
    if reference.startswith("#"):
        project_id = runtime.resolve_project_id(client, state, project)
        return client.bugs.get_by_number(project_id, int(reference[1:]))
    return client.bugs.get(int(reference))


def _parse_tags(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    if not raw.strip():
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _build_update_payload(**fields) -> dict:
    payload: dict = {}
    for key, value in fields.items():
        if value is None:
            continue
        if key == "tags":
            payload[key] = _parse_tags(value) or []
        else:
            payload[key] = value
    return payload


def _resolve_comment_body(body: str | None, file: Path | None) -> str:
    if file is not None:
        return file.read_text()
    if body is None or body == STDIN_MARKER:
        return sys.stdin.read()
    return body
