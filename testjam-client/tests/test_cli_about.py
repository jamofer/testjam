"""CLI smoke for `testjam about`.

Patches `runtime.build_client` so the command receives a fake SDK whose
`.about.get()` returns a canned `ServerAbout`. No backend dependency.
"""
from __future__ import annotations

import json
from contextlib import nullcontext

import httpx
import pytest
from typer.testing import CliRunner

from testjam_client.cli import app
from testjam_client.resources.about import ServerAbout


runner = CliRunner()


@pytest.fixture
def cli_config(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(config_file))
    config_file.write_text('[profiles.default]\nurl = "http://testserver/api/v1"\n')


def test_about_prints_client_and_server_metadata(cli_config, monkeypatch):
    monkeypatch.setattr(
        "testjam_client.cli.commands.about.runtime.build_client",
        lambda state: _FakeClient(_sample()),
    )

    result = runner.invoke(app, ["--json", "about"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["client_version"]
    assert payload["server_url"] == "http://testserver/api/v1"
    assert payload["server_status"] == "ok"
    assert payload["server_version"] == "1.0.0"
    assert payload["server_ref"] == "v1.0.0"
    assert payload["server_commit"] == "abc1234"
    assert payload["server_built_at"] == "2026-05-25T12:00:00Z"


def test_about_falls_back_to_unreachable_on_network_error(cli_config, monkeypatch):
    def boom(state):
        raise httpx.ConnectError("nope")

    monkeypatch.setattr(
        "testjam_client.cli.commands.about.runtime.build_client",
        boom,
    )

    result = runner.invoke(app, ["--json", "about"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["server_status"] == "unreachable"
    assert payload["server_version"] == "unknown"
    assert payload["client_version"]


def test_about_falls_back_when_no_profile_url(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(config_file))
    config_file.write_text('[profiles.default]\n')

    result = runner.invoke(app, ["--json", "about"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["server_status"] == "unreachable"
    assert payload["server_url"] is None


def _sample() -> ServerAbout:
    return ServerAbout(
        version="1.0.0",
        ref="v1.0.0",
        commit="abc1234",
        built_at="2026-05-25T12:00:00Z",
    )


class _FakeAbout:
    def __init__(self, payload: ServerAbout) -> None:
        self._payload = payload

    def get(self) -> ServerAbout:
        return self._payload


class _FakeClient:
    def __init__(self, payload: ServerAbout) -> None:
        self.about = _FakeAbout(payload)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None
