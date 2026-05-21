"""Testjam command-line client entry point."""
from importlib.metadata import PackageNotFoundError, version

import typer

from testjam_client.cli.commands import auth as auth_commands
from testjam_client.cli.commands import bugs as bug_commands
from testjam_client.cli.commands import cases as case_commands
from testjam_client.cli.commands import config as config_commands
from testjam_client.cli.commands import executions as execution_commands
from testjam_client.cli.commands import plans as plan_commands
from testjam_client.cli.commands import projects as project_commands
from testjam_client.cli.commands import suites as suite_commands
from testjam_client.cli.config import ConfigStore, default_config_path
from testjam_client.cli.state import CliState


PACKAGE_NAME = "testjam-client"
FALLBACK_VERSION = "0.0.0"
API_KEY_ENV_VAR = "TESTJAM_API_KEY"

app = typer.Typer(
    name="testjam",
    help="Testjam command-line client.",
    no_args_is_help=True,
)


def main() -> None:
    app()


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


@app.callback()
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
) -> None:
    """Testjam command-line client."""
    store = ConfigStore(default_config_path())
    context.obj = CliState(
        config=store,
        profile_name=profile or store.default_profile,
        api_key_override=api_key,
        project_override=project,
        json_output=json_output,
    )


auth_commands.register(app)
app.add_typer(config_commands.build_app())
app.add_typer(project_commands.build_app())
app.add_typer(suite_commands.build_app())
app.add_typer(case_commands.build_app())
app.add_typer(plan_commands.build_app())
app.add_typer(execution_commands.build_app())
app.add_typer(bug_commands.build_app())
