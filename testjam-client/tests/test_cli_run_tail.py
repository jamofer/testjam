"""Tests for `testjam run tail` — polling loop + exit codes."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from testjam_client.cli import app
from testjam_client.cli.commands import run as run_command

runner = CliRunner()


@pytest.fixture
def cli_state(auth_client, tmp_path, monkeypatch) -> dict:
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(config_file))
    config_file.write_text(
        '[profiles.default]\n'
        'url = "http://testserver/api/v1"\n'
    )

    monkeypatch.setattr(auth_client, "close", lambda: None)
    monkeypatch.setattr(
        "testjam_client.cli.runtime.build_client",
        lambda state: auth_client,
    )
    monkeypatch.setattr("testjam_client.cli.commands.run.time.sleep", lambda _: None)

    project = auth_client.projects.create("Demo")
    suite = auth_client.suites.create(project["id"], name="S1")
    case_one = auth_client.cases.create(suite["id"], name="C1")
    case_two = auth_client.cases.create(suite["id"], name="C2")

    return {
        "client": auth_client,
        "project": project,
        "suite": suite,
        "cases": [case_one, case_two],
    }


@pytest.fixture
def clock(monkeypatch):
    now = {"seconds": 0.0}

    def advance(seconds):
        now["seconds"] += seconds

    monkeypatch.setattr("testjam_client.cli.commands.run.time.monotonic", lambda: now["seconds"])
    monkeypatch.setattr("testjam_client.cli.commands.run.time.sleep", advance)
    return now


def test_start_with_plan_runs_the_plan_cases(cli_state):
    sdk = cli_state["client"]
    case_ids = [case["id"] for case in cli_state["cases"]]
    plan = sdk.plans.create(cli_state["project"]["id"], "Sprint", test_case_ids=case_ids)

    result = runner.invoke(
        app, ["--yes", "--json", "run", "start", "Nightly", "--project", "Demo", "--plan", str(plan["id"])],
    )

    execution_id = json.loads(result.output)["id"]
    assert len(sdk.executions.list_results(execution_id)) == len(case_ids)


def test_tail_returns_zero_when_all_results_pass(cli_state):
    execution_id = _seed_execution(cli_state, statuses=["passed", "passed"], terminal="completed")

    result = runner.invoke(app, ["run", "tail", str(execution_id)])

    assert result.exit_code == 0


def test_tail_returns_one_when_any_result_fails(cli_state):
    execution_id = _seed_execution(cli_state, statuses=["passed", "failed"], terminal="completed")

    result = runner.invoke(app, ["run", "tail", str(execution_id)])

    assert result.exit_code == 1


def test_tail_returns_two_when_execution_aborted(cli_state):
    execution_id = _seed_execution(cli_state, statuses=["passed", "passed"], terminal="aborted")

    result = runner.invoke(app, ["run", "tail", str(execution_id)])

    assert result.exit_code == 2


def test_tail_json_emits_snapshot(cli_state):
    execution_id = _seed_execution(cli_state, statuses=["passed", "passed"], terminal="completed")

    result = runner.invoke(app, ["--json", "run", "tail", str(execution_id)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["execution"]["id"] == execution_id
    assert len(payload["results"]) == 2


def test_tail_rides_out_network_blips(cli_state, clock, monkeypatch):
    execution_id = _seed_execution(cli_state, statuses=["passed", "passed"], terminal="completed")
    _fail_first_fetches(cli_state["client"], monkeypatch, failures=2)

    result = runner.invoke(app, ["run", "tail", str(execution_id)])

    assert result.exit_code == 0


def test_tail_gives_up_when_the_server_stays_unreachable(cli_state, clock, monkeypatch):
    execution_id = _seed_execution(cli_state, statuses=["passed", "passed"], terminal="completed")
    _fail_first_fetches(cli_state["client"], monkeypatch, failures=10_000)

    result = runner.invoke(app, ["run", "tail", str(execution_id), "--interval", "10"])

    assert result.exit_code == run_command.EXIT_UNREACHABLE


def test_tail_stops_at_the_timeout(cli_state, clock):
    execution_id = _seed_execution(cli_state, statuses=["passed", "passed"], terminal="in_progress")

    result = runner.invoke(app, ["run", "tail", str(execution_id), "--timeout", "30", "--interval", "5"])

    assert result.exit_code == run_command.EXIT_TIMED_OUT
    assert clock["seconds"] == 30


def _fail_first_fetches(client, monkeypatch, failures: int) -> None:
    real_get = client.executions.get
    remaining = {"failures": failures}

    def flaky_get(execution_id):
        if remaining["failures"]:
            remaining["failures"] -= 1
            raise httpx.ConnectError("connection refused")
        return real_get(execution_id)

    monkeypatch.setattr(client.executions, "get", flaky_get)


def _seed_execution(cli_state: dict, *, statuses: list[str], terminal: str) -> int:
    sdk = cli_state["client"]
    case_ids = [case["id"] for case in cli_state["cases"]]

    execution = sdk.executions.create(
        cli_state["project"]["id"],
        title="Tail run",
        type="manual",
        test_case_ids=case_ids,
    )
    for result, status in zip(sdk.executions.list_results(execution["id"]), statuses):
        sdk.results.update(result["id"], status=status)
    sdk.executions.update(execution["id"], status=terminal)
    return execution["id"]
