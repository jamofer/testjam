"""Live-API smoke tests for the `testjam` CLI binary.

Skipped unless ``TESTJAM_E2E_LIVE`` is set (the ``make test-cli-e2e`` target
sets it after ensuring the api container is up and an admin exists). Each
case invokes the installed ``testjam`` entry point against
``http://localhost:8000/api/v1``.
"""
from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest


LIVE_FLAG_ENV = "TESTJAM_E2E_LIVE"
BASE_URL = os.environ.get("TESTJAM_E2E_URL", "http://localhost:8000/api/v1")
ADMIN_USER = os.environ.get("TESTJAM_E2E_USER", "admin")
ADMIN_PASSWORD = os.environ.get("TESTJAM_E2E_PASSWORD", "admin123")

pytestmark = pytest.mark.skipif(
    not os.environ.get(LIVE_FLAG_ENV),
    reason=f"Set {LIVE_FLAG_ENV}=1 (or run `make test-cli-e2e`) to enable.",
)


@pytest.fixture
def cli(tmp_path):
    config_file = tmp_path / "config.toml"
    environment = {"TESTJAM_CONFIG": str(config_file)}
    runner = _CliRunner(environment)

    runner.run("config", "set", "url", BASE_URL)
    runner.run("login", "-u", ADMIN_USER, "-p", ADMIN_PASSWORD)

    return runner


def test_login_persists_token_in_config(cli):
    config_text = (cli.config_path).read_text()

    assert "token" in config_text
    assert BASE_URL in config_text


def test_project_create_then_appears_in_list(cli):
    name = f"smoke-project-{uuid.uuid4().hex[:8]}"

    create_result = cli.run("project", "create", name)
    list_result = cli.run("--json", "project", "list")

    assert name in create_result.stdout
    assert name in list_result.stdout


def test_bug_create_show_and_comment_roundtrip(cli):
    project_name = f"smoke-bug-{uuid.uuid4().hex[:8]}"
    cli.run("project", "create", project_name)
    cli.run("config", "set", "default_project", project_name)

    create_result = cli.run(
        "--json", "bug", "create", "Smoke bug", "--severity", "high",
    )
    bug_id = _extract_id(create_result.stdout)

    show_result = cli.run("--json", "bug", "show", str(bug_id))
    comment_result = cli.run("bug", "comment", "add", str(bug_id), "hello from smoke")

    assert '"title": "Smoke bug"' in show_result.stdout
    assert '"severity": "high"' in show_result.stdout
    assert "hello from smoke" in comment_result.stdout


class _CliRunner:
    def __init__(self, environment: dict[str, str]) -> None:
        self._environment = environment

    @property
    def config_path(self) -> Path:
        return Path(self._environment["TESTJAM_CONFIG"])

    def run(self, *args: str) -> subprocess.CompletedProcess:
        merged = dict(os.environ, **self._environment)
        return subprocess.run(
            ["testjam", *args],
            env=merged,
            capture_output=True,
            text=True,
            check=True,
        )


def _extract_id(json_blob: str) -> int:
    parsed = json.loads(json_blob)
    return parsed["id"]
