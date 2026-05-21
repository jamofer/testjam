"""Smoke tests for the write commands.

Same pattern as ``test_cli_read_commands.py``: in-process FastAPI app via
``auth_client``, ``runtime.build_client`` patched to hand the seeded SDK to
the CLI, write commands invoked end-to-end, side-effects verified against
the same SDK.
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
    config_file.write_text(
        '[profiles.default]\n'
        'url = "http://testserver/api/v1"\n'
        'default_project = "Demo"\n'
    )

    monkeypatch.setattr(auth_client, "close", lambda: None)
    monkeypatch.setattr(
        "testjam_client.cli.runtime.build_client",
        lambda state: auth_client,
    )

    project = auth_client.projects.create("Demo")
    suite = auth_client.suites.create(project["id"], name="Suite A")

    return {
        "client": auth_client,
        "project": project,
        "suite": suite,
        "config_file": config_file,
        "tmp_path": tmp_path,
    }


def test_project_create_persists_new_project(cli_state):
    result = runner.invoke(app, ["project", "create", "Brand New"])

    assert result.exit_code == 0
    assert "Brand New" in result.output
    listed = cli_state["client"].projects.list()
    assert any(row["name"] == "Brand New" for row in listed)


def test_case_create_without_steps(cli_state):
    suite_id = cli_state["suite"]["id"]

    result = runner.invoke(
        app, ["case", "create", "Login flow", "--suite", str(suite_id)],
    )

    assert result.exit_code == 0
    assert "Login flow" in result.output


def test_case_create_with_steps_file(cli_state):
    suite_id = cli_state["suite"]["id"]
    steps_file = cli_state["tmp_path"] / "steps.txt"
    steps_file.write_text(
        "open the login page => form visible\n"
        "submit credentials => redirected to dashboard\n"
    )

    result = runner.invoke(
        app,
        ["case", "create", "Login", "--suite", str(suite_id), "--steps", str(steps_file)],
    )

    assert result.exit_code == 0
    new_case_id = _extract_id(result.output, cli_state)
    steps = cli_state["client"].cases.list_steps(new_case_id)
    actions = [step["action"] for step in steps]
    assert "open the login page" in actions
    assert "submit credentials" in actions


def test_case_create_with_json_steps(cli_state):
    suite_id = cli_state["suite"]["id"]
    steps_file = cli_state["tmp_path"] / "steps.json"
    steps_file.write_text(json.dumps([
        {"action": "click button", "expected_result": "modal opens"},
    ]))

    result = runner.invoke(
        app,
        ["case", "create", "Click", "--suite", str(suite_id), "--steps", str(steps_file)],
    )

    assert result.exit_code == 0
    case_id = _extract_id(result.output, cli_state)
    steps = cli_state["client"].cases.list_steps(case_id)
    assert steps[0]["action"] == "click button"
    assert steps[0]["expected_result"] == "modal opens"


def test_plan_create_under_project(cli_state):
    result = runner.invoke(
        app, ["plan", "create", "Release 1.0", "--description", "smoke tests"],
    )

    assert result.exit_code == 0
    assert "Release 1.0" in result.output


def test_run_start_confirm_required_without_yes(cli_state):
    case = cli_state["client"].cases.create(cli_state["suite"]["id"], name="C1")

    result = runner.invoke(
        app,
        ["run", "start", "Nightly", "--cases", str(case["id"])],
        input="n\n",
    )

    assert result.exit_code != 0


def test_run_start_with_yes_creates_execution(cli_state):
    case = cli_state["client"].cases.create(cli_state["suite"]["id"], name="C1")

    result = runner.invoke(
        app,
        ["--yes", "run", "start", "Nightly", "--cases", str(case["id"])],
    )

    assert result.exit_code == 0
    assert "Nightly" in result.output


def test_bug_create_basic(cli_state):
    result = runner.invoke(
        app,
        ["bug", "create", "Login broken", "--severity", "high", "--tags", "auth,login"],
    )

    assert result.exit_code == 0
    assert "Login broken" in result.output


def test_bug_update_changes_fields(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="Original", severity="low",
    )

    result = runner.invoke(
        app,
        ["bug", "update", str(bug["id"]), "--title", "Renamed", "--severity", "high"],
    )

    assert result.exit_code == 0
    refreshed = cli_state["client"].bugs.get(bug["id"])
    assert refreshed["title"] == "Renamed"
    assert refreshed["severity"] == "high"


def test_bug_update_without_fields_exits_two(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="A", severity="low",
    )

    result = runner.invoke(app, ["bug", "update", str(bug["id"])])

    assert result.exit_code == 2
    assert "nothing to update" in result.output.lower()


def test_bug_comment_add_with_inline_body(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="B", severity="low",
    )

    result = runner.invoke(
        app, ["bug", "comment", "add", str(bug["id"]), "first comment"],
    )

    assert result.exit_code == 0
    comments = cli_state["client"].bugs.list_comments(bug["id"])
    assert any(comment["body"] == "first comment" for comment in comments)


def test_bug_comment_add_from_file(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="C", severity="low",
    )
    comment_file = cli_state["tmp_path"] / "comment.md"
    comment_file.write_text("multi\nline\ncomment\n")

    result = runner.invoke(
        app,
        ["bug", "comment", "add", str(bug["id"]), "--file", str(comment_file)],
    )

    assert result.exit_code == 0
    comments = cli_state["client"].bugs.list_comments(bug["id"])
    assert any("multi" in comment["body"] for comment in comments)


def test_bug_status_change_requires_confirm(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="D", severity="low",
    )

    result = runner.invoke(
        app, ["bug", "status", "change", str(bug["id"]), "in_progress"], input="n\n",
    )

    assert result.exit_code != 0


def test_bug_status_change_with_yes(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="E", severity="low",
    )

    result = runner.invoke(
        app,
        ["--yes", "bug", "status", "change", str(bug["id"]), "in_progress"],
    )

    assert result.exit_code == 0
    refreshed = cli_state["client"].bugs.get(bug["id"])
    assert refreshed["status"] == "in_progress"


def test_bug_watch_and_unwatch(cli_state):
    bug = cli_state["client"].bugs.create(
        cli_state["project"]["id"], title="F", severity="low",
    )

    watch_result = runner.invoke(app, ["bug", "watch", str(bug["id"])])
    unwatch_result = runner.invoke(app, ["bug", "unwatch", str(bug["id"])])

    assert watch_result.exit_code == 0
    assert unwatch_result.exit_code == 0
    assert "watching" in watch_result.output.lower()
    assert "no longer" in unwatch_result.output.lower()


def _extract_id(output: str, cli_state: dict) -> int:
    cases = cli_state["client"].cases.list(cli_state["suite"]["id"])
    return cases[-1]["id"]
