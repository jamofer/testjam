"""Smoke tests for the read commands (`project|suite|case|plan|execution|bug`).

Each command is exercised against the in-process FastAPI app via the
``auth_client`` fixture, with ``runtime.build_client`` patched to hand the
existing SDK to the CLI instead of building a real HTTP transport.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from testjam_client.cli import app

runner = CliRunner()


@pytest.fixture
def cli_state(auth_client, tmp_path, monkeypatch) -> dict:
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(config_file))
    config_file.write_text('[profiles.default]\nurl = "http://testserver/api/v1"\n')

    monkeypatch.setattr(auth_client, "close", lambda: None)
    monkeypatch.setattr(
        "testjam_client.cli.runtime.build_client",
        lambda state: auth_client,
    )

    project = auth_client.projects.create("Demo Project")
    suite = auth_client.suites.create(project["id"], name="Smoke")
    case = auth_client.cases.create(suite["id"], name="Login flow")
    plan = auth_client.plans.create(project["id"], "Sprint 1")
    execution = auth_client.executions.create(
        project["id"], title="CI run", type="manual", test_case_ids=[case["id"]],
    )
    bug = auth_client.bugs.create(project["id"], title="Login broken", severity="high")

    return {
        "project": project,
        "suite": suite,
        "case": case,
        "plan": plan,
        "execution": execution,
        "bug": bug,
        "config_file": config_file,
    }


def test_project_list_includes_seeded_project(cli_state):
    result = runner.invoke(app, ["project", "list"])

    assert result.exit_code == 0
    assert "Demo Project" in result.output


def test_project_show_resolves_by_name(cli_state):
    result = runner.invoke(app, ["project", "show", "Demo Project"])

    assert result.exit_code == 0
    assert "Demo Project" in result.output


def test_project_show_resolves_by_id(cli_state):
    project_id = cli_state["project"]["id"]

    result = runner.invoke(app, ["project", "show", str(project_id)])

    assert result.exit_code == 0
    assert str(project_id) in result.output


def test_json_flag_emits_parseable_json(cli_state):
    result = runner.invoke(app, ["--json", "project", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert any(row["name"] == "Demo Project" for row in payload)


def test_suite_list_uses_default_project(cli_state):
    _set_default_project(cli_state["config_file"], "Demo Project")

    result = runner.invoke(app, ["suite", "list"])

    assert result.exit_code == 0
    assert "Smoke" in result.output


def test_suite_list_accepts_project_override(cli_state):
    result = runner.invoke(app, ["suite", "list", "--project", "Demo Project"])

    assert result.exit_code == 0
    assert "Smoke" in result.output


def test_suite_show_renders_suite_by_id(cli_state):
    suite_id = cli_state["suite"]["id"]

    result = runner.invoke(app, ["suite", "show", str(suite_id)])

    assert result.exit_code == 0
    assert "Smoke" in result.output


def test_case_list_requires_suite_id(cli_state):
    suite_id = cli_state["suite"]["id"]

    result = runner.invoke(app, ["case", "list", "--suite", str(suite_id)])

    assert result.exit_code == 0
    assert "Login flow" in result.output


def test_case_show_renders_case_by_id(cli_state):
    case_id = cli_state["case"]["id"]

    result = runner.invoke(app, ["case", "show", str(case_id)])

    assert result.exit_code == 0
    assert "Login flow" in result.output


def test_plan_list_under_project(cli_state):
    result = runner.invoke(app, ["plan", "list", "--project", "Demo Project"])

    assert result.exit_code == 0
    assert "Sprint 1" in result.output


def test_plan_show_renders_plan_by_id(cli_state):
    plan_id = cli_state["plan"]["id"]

    result = runner.invoke(app, ["plan", "show", str(plan_id)])

    assert result.exit_code == 0
    assert "Sprint 1" in result.output


def test_execution_list_under_project(cli_state):
    result = runner.invoke(
        app, ["execution", "list", "--project", "Demo Project"],
    )

    assert result.exit_code == 0
    assert "CI run" in result.output


def test_execution_show_renders_execution_by_id(cli_state):
    execution_id = cli_state["execution"]["id"]

    result = runner.invoke(app, ["execution", "show", str(execution_id)])

    assert result.exit_code == 0
    assert "CI run" in result.output


def test_bug_list_under_project(cli_state):
    result = runner.invoke(app, ["bug", "list", "--project", "Demo Project"])

    assert result.exit_code == 0
    assert "Login broken" in result.output


def test_bug_show_by_id(cli_state):
    bug_id = cli_state["bug"]["id"]

    result = runner.invoke(app, ["bug", "show", str(bug_id)])

    assert result.exit_code == 0
    assert "Login broken" in result.output


def test_bug_show_by_number_requires_project(cli_state):
    bug_number = cli_state["bug"]["number"]

    result = runner.invoke(
        app,
        ["bug", "show", f"#{bug_number}", "--project", "Demo Project"],
    )

    assert result.exit_code == 0
    assert "Login broken" in result.output


def test_missing_project_raises_bad_parameter(cli_state):
    result = runner.invoke(app, ["suite", "list"])

    assert result.exit_code != 0
    assert "project" in result.output.lower()


def _set_default_project(config_file: Path, project_name: str) -> None:
    config_file.write_text(
        '[profiles.default]\n'
        'url = "http://testserver/api/v1"\n'
        f'default_project = "{project_name}"\n'
    )
