"""Render command results as a Rich table or raw JSON.

Every read command funnels its payload through :func:`render` so the
``--json`` global flag is honoured uniformly.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

import typer
from rich.console import Console
from rich.table import Table


console = Console()


def render(
    payload: Any,
    *,
    columns: Sequence[str],
    json_mode: bool,
) -> None:
    if json_mode:
        typer.echo(json.dumps(payload, indent=2, default=str))
        return
    if isinstance(payload, list):
        _render_table(payload, columns)
        return
    if isinstance(payload, dict):
        _render_object(payload, columns)
        return
    typer.echo(str(payload))


def _render_table(rows: list[dict[str, Any]], columns: Sequence[str]) -> None:
    table = Table(show_header=True, header_style="bold")
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*[_stringify(row.get(column)) for column in columns])
    console.print(table)


def _render_object(payload: dict[str, Any], columns: Sequence[str]) -> None:
    keys = list(columns) if columns else list(payload)
    table = Table(show_header=False)
    table.add_column("field", style="bold")
    table.add_column("value")
    for key in keys:
        table.add_row(key, _stringify(payload.get(key)))
    console.print(table)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)
