"""Tests for `testjam config` and the underlying ConfigStore."""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from testjam_client.cli import app

runner = CliRunner()


@pytest.fixture
def config_path(tmp_path, monkeypatch) -> Path:
    target = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(target))
    return target


def test_set_creates_default_profile_and_persists(config_path):
    result = runner.invoke(app, ["config", "set", "url", "https://srv.example/api/v1"])

    assert result.exit_code == 0
    content = config_path.read_text()
    assert "[profiles.default]" in content
    assert "https://srv.example/api/v1" in content


def test_show_masks_token(config_path):
    config_path.write_text(
        '[profiles.default]\n'
        'url = "https://srv.example/api/v1"\n'
        'token = "eyJabcdef1234567890"\n'
    )

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "eyJabcdef1234567890" not in result.output
    assert "eyJa" in result.output and "7890" in result.output
    assert "https://srv.example/api/v1" in result.output


def test_show_empty_profile_reports_empty(config_path):
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "(empty)" in result.output


def test_set_rejects_unknown_key(config_path):
    result = runner.invoke(app, ["config", "set", "bogus", "x"])

    assert result.exit_code == 2
    assert "unknown key" in result.output.lower()


def test_set_empty_value_clears_field(config_path):
    config_path.write_text(
        '[profiles.default]\nurl = "https://srv.example/api/v1"\n'
    )

    result = runner.invoke(app, ["config", "set", "url", ""])

    assert result.exit_code == 0
    assert "https://srv.example/api/v1" not in config_path.read_text()


def test_profile_flag_targets_named_profile(config_path):
    runner.invoke(app, ["--profile", "ci", "config", "set", "url", "https://ci.example/api/v1"])

    content = config_path.read_text()
    assert "[profiles.ci]" in content
    assert "https://ci.example/api/v1" in content


def test_profile_flag_does_not_leak_into_default(config_path):
    runner.invoke(app, ["--profile", "ci", "config", "set", "url", "https://ci.example/api/v1"])

    result = runner.invoke(app, ["config", "show"])

    assert "https://ci.example" not in result.output
    assert "(empty)" in result.output
