"""Tests for the REPL entry point and history path resolver."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from testjam_client.cli import app
from testjam_client.cli import repl as repl_module

runner = CliRunner()


@pytest.fixture
def isolated_config(tmp_path, monkeypatch) -> Path:
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(config_file))
    return config_file


@pytest.fixture
def repl_spy(monkeypatch) -> dict:
    record: dict = {"called": False}

    def spy(context):
        record["called"] = True
        record["context"] = context

    monkeypatch.setattr("testjam_client.cli.enter_repl", spy)
    return record


def test_zero_args_invokes_repl(isolated_config, repl_spy):
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert repl_spy["called"] is True


def test_repl_subcommand_invokes_repl(isolated_config, repl_spy):
    result = runner.invoke(app, ["repl"])

    assert result.exit_code == 0
    assert repl_spy["called"] is True


def test_subcommand_does_not_invoke_repl(isolated_config, repl_spy):
    runner.invoke(app, ["config", "show"])

    assert repl_spy["called"] is False


def test_history_path_lives_under_user_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(repl_module.platformdirs, "user_data_dir", lambda name: str(tmp_path / name))

    path = repl_module._history_path()

    assert path == tmp_path / "testjam" / "history"
