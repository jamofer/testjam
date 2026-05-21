"""Testjam command-line client entry point."""
import sys
from importlib.metadata import PackageNotFoundError, version

import httpx
import typer

from testjam_client.cli.commands import auth as auth_commands
from testjam_client.cli.commands import bugs as bug_commands
from testjam_client.cli.commands import cases as case_commands
from testjam_client.cli.commands import config as config_commands
from testjam_client.cli.commands import executions as execution_commands
from testjam_client.cli.commands import plans as plan_commands
from testjam_client.cli.commands import projects as project_commands
from testjam_client.cli.commands import run as run_commands
from testjam_client.cli.commands import suites as suite_commands
from testjam_client.cli import output
from testjam_client.cli.config import ConfigStore, default_config_path
from testjam_client.cli.repl import enter_repl
from testjam_client.cli.state import CliState
from testjam_client.errors import TestjamError


PACKAGE_NAME = "testjam-client"
FALLBACK_VERSION = "0.0.0"
API_KEY_ENV_VAR = "TESTJAM_API_KEY"
EXIT_INTERRUPTED = 130

app = typer.Typer(
    name="testjam",
    help="Testjam command-line client.",
)


def main() -> None:
    run_with_pretty_errors(app)


def run_with_pretty_errors(callable_app) -> None:
    try:
        callable_app()
    except TestjamError as exc:
        output.console.print(f"[bold red]Error[/bold red]: {exc}")
        sys.exit(1)
    except httpx.HTTPError as exc:
        output.console.print(f"[bold red]Network error[/bold red]: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        output.console.print("[yellow]Interrupted.[/yellow]")
        sys.exit(EXIT_INTERRUPTED)


def _resolve_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return FALLBACK_VERSION


def _version_callback(value: bool) -> None:
    if not value:
        return
    typer.echo(f"testjam {_resolve_version()}")
    raise typer.Exit()


@app.callback(invoke_without_command=True)
def root(
    context: typer.Context,
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the testjam CLI version and exit.",
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        help="Config profile to use. Defaults to the file's default_profile.",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar=API_KEY_ENV_VAR,
        help="Project-scoped API key for this invocation. Overrides the profile.",
    ),
    project: str | None = typer.Option(
        None,
        "--project",
        help="Project name or id. Overrides profile.default_project.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON instead of a Rich table.",
    ),
    yes_to_all: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompts (assume 'yes').",
    ),
) -> None:
    """Testjam command-line client."""
    store = ConfigStore(default_config_path())
    context.obj = CliState(
        config=store,
        profile_name=profile or store.default_profile,
        api_key_override=api_key,
        project_override=project,
        json_output=json_output,
        yes_to_all=yes_to_all,
    )
    if context.invoked_subcommand is None:
        enter_repl(context)


@app.command("repl", help="Enter the interactive shell (same as running `testjam` with no args).")
def repl_command(context: typer.Context) -> None:
    enter_repl(context)


auth_commands.register(app)
app.add_typer(config_commands.build_app())
app.add_typer(project_commands.build_app())
app.add_typer(suite_commands.build_app())
app.add_typer(case_commands.build_app())
app.add_typer(plan_commands.build_app())
app.add_typer(execution_commands.build_app())
app.add_typer(run_commands.build_app())
app.add_typer(bug_commands.build_app())
