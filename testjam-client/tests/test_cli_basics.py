"""Smoke tests for the `testjam` CLI entry point."""
from importlib.metadata import version

from typer.testing import CliRunner

from testjam_client.cli import app

runner = CliRunner()


def test_version_flag_prints_package_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert version("testjam-client") in result.output


def test_help_lists_command_name():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "testjam" in result.output.lower()
