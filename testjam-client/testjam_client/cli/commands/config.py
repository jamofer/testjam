"""`testjam config` — inspect and edit the active profile."""
from __future__ import annotations

import typer

from testjam_client.cli.config import EDITABLE_FIELDS, SECRET_FIELDS, mask_secret
from testjam_client.cli.state import CliState


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="config",
        help="Inspect and edit the active profile.",
        no_args_is_help=True,
    )
    app.command("show", help="Print the active profile (secrets masked).")(show)
    app.command("set", help="Set a field on the active profile.")(set_value)
    return app


def show(context: typer.Context) -> None:
    state: CliState = context.obj
    profile = state.profile

    typer.echo(f"profile: {state.profile_name}")
    typer.echo(f"path: {state.config.path}")
    if not profile:
        typer.echo("(empty)")
        return
    for key in sorted(profile):
        raw = profile[key]
        display = mask_secret(raw) if key in SECRET_FIELDS else raw
        typer.echo(f"{key} = {display}")


def set_value(
    context: typer.Context,
    key: str = typer.Argument(..., help=f"One of: {sorted(EDITABLE_FIELDS)}"),
    value: str = typer.Argument(..., help="New value. Use '' to clear."),
) -> None:
    if key not in EDITABLE_FIELDS:
        typer.echo(
            f"unknown key '{key}'. Allowed: {sorted(EDITABLE_FIELDS)}", err=True
        )
        raise typer.Exit(code=2)
    state: CliState = context.obj
    state.config.set_profile_value(state.profile_name, key, value or None)
    state.config.save()
    typer.echo(f"{key} updated in profile {state.profile_name}")
