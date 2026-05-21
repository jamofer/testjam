"""`testjam login` / `testjam logout` — credential exchange + cache."""
from __future__ import annotations

import typer

from testjam_client import TestjamClient
from testjam_client.cli.state import CliState


def register(app: typer.Typer) -> None:
    app.command("login", help="Log in against a Testjam server and cache the JWT.")(login)
    app.command("logout", help="Drop the cached JWT for the active profile.")(logout)


def login(
    context: typer.Context,
    username: str = typer.Option(..., "-u", "--username", prompt=True),
    password: str = typer.Option(
        ..., "-p", "--password", prompt=True, hide_input=True, confirmation_prompt=False
    ),
    url: str | None = typer.Option(
        None, "--url", help="Server base URL up to /api/v1. Defaults to the profile value.",
    ),
) -> None:
    state: CliState = context.obj
    base_url = url or state.profile.get("url") or typer.prompt("Server URL")

    with TestjamClient(base_url) as client:
        token = client.login(username, password)

    state.config.set_profile_value(state.profile_name, "url", base_url)
    state.config.set_profile_value(state.profile_name, "username", username)
    state.config.set_profile_value(state.profile_name, "token", token)
    state.config.save()
    typer.echo(f"Logged in as {username} to {base_url} (profile {state.profile_name})")


def logout(context: typer.Context) -> None:
    state: CliState = context.obj
    if not state.profile.get("token"):
        typer.echo(f"No cached token in profile {state.profile_name}")
        return
    state.config.set_profile_value(state.profile_name, "token", None)
    state.config.save()
    typer.echo(f"Logged out (profile {state.profile_name})")
