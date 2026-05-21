"""Tests for `testjam login` / `testjam logout`."""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from testjam_client.cli import app
from testjam_client.cli.commands import auth as auth_commands

runner = CliRunner()


@pytest.fixture
def config_path(tmp_path, monkeypatch) -> Path:
    target = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(target))
    return target


@pytest.fixture
def fake_login(monkeypatch):
    recorded: dict[str, str] = {}

    def factory(base_url: str, **_kwargs):
        recorded["base_url"] = base_url
        return FakeTestjamClient(base_url, recorded)

    monkeypatch.setattr(auth_commands, "TestjamClient", factory)
    return recorded


def test_login_stores_url_username_and_token(config_path, fake_login):
    result = runner.invoke(
        app,
        ["login", "--url", "https://srv.example/api/v1", "--username", "alice", "--password", "pw"],
    )

    assert result.exit_code == 0
    assert fake_login["username"] == "alice"
    assert fake_login["password"] == "pw"
    content = config_path.read_text()
    assert "https://srv.example/api/v1" in content
    assert 'username = "alice"' in content
    assert 'token = "fake-jwt-token"' in content


def test_login_targets_named_profile(config_path, fake_login):
    runner.invoke(
        app,
        [
            "--profile", "ci",
            "login",
            "--url", "https://ci.example/api/v1",
            "--username", "bot",
            "--password", "pw",
        ],
    )

    content = config_path.read_text()
    assert "[profiles.ci]" in content
    assert 'username = "bot"' in content


def test_login_reuses_profile_url_when_flag_omitted(config_path, fake_login):
    config_path.write_text(
        '[profiles.default]\nurl = "https://stored.example/api/v1"\n'
    )

    result = runner.invoke(
        app,
        ["login", "--username", "alice", "--password", "pw"],
    )

    assert result.exit_code == 0
    assert fake_login["base_url"] == "https://stored.example/api/v1"


def test_logout_clears_token(config_path, fake_login):
    runner.invoke(
        app,
        ["login", "--url", "https://srv.example/api/v1", "--username", "alice", "--password", "pw"],
    )

    result = runner.invoke(app, ["logout"])

    assert result.exit_code == 0
    assert "token" not in config_path.read_text()


def test_logout_without_token_is_noop(config_path):
    result = runner.invoke(app, ["logout"])

    assert result.exit_code == 0
    assert "no cached token" in result.output.lower()


class FakeTestjamClient:
    def __init__(self, base_url: str, recorder: dict[str, str]) -> None:
        self.base_url = base_url
        self._recorder = recorder

    def login(self, username: str, password: str) -> str:
        self._recorder["username"] = username
        self._recorder["password"] = password
        return "fake-jwt-token"

    def __enter__(self) -> "FakeTestjamClient":
        return self

    def __exit__(self, *exc_info) -> None:
        return None
