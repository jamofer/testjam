"""Listener event flow against the in-process backend."""
from types import SimpleNamespace

import pytest

from testjam_client.listener import listener as listener_module
from testjam_client.listener.listener import TestjamListener

PROJECT_NAME = "Listener Flow"


@pytest.fixture
def listener(auth_client, monkeypatch):
    monkeypatch.setenv("TESTJAM_API_KEY", "unused-by-the-in-process-client")
    monkeypatch.setenv("TESTJAM_PROJECT", PROJECT_NAME)
    monkeypatch.setattr(listener_module, "TestjamClient", lambda *args, **kwargs: auth_client)
    return TestjamListener()


@pytest.fixture
def robot_file(tmp_path):
    path = tmp_path / "login.robot"
    path.write_text("*** Test Cases ***\n")
    return path


def test_file_root_suite_reports_its_tests(listener, auth_client, robot_file):
    _run_suite(listener, _suite("Login", robot_file), _test("Valid Login", ["Open App"]), "PASS")

    results = auth_client.executions.list_results(listener.execution_id)
    assert [(result["test_case_title"], result["status"]) for result in results] == [
        ("Valid Login", "passed"),
    ]


def test_file_root_suite_becomes_top_level_suite(listener, auth_client, robot_file):
    _run_suite(listener, _suite("Login", robot_file), _test("Valid Login", ["Open App"]), "PASS")

    suites = auth_client.suites.list(listener.project_id)
    assert [suite["name"] for suite in suites] == ["Login"]


def test_directory_root_suite_is_not_reported(listener, auth_client, robot_file):
    directory_suite = _suite("Suites", robot_file.parent)
    listener.start_suite(directory_suite, None)

    _run_suite(listener, _suite("Login", robot_file), _test("Valid Login", ["Open App"]), "PASS")
    listener.end_suite(directory_suite, None)

    suites = auth_client.suites.list(listener.project_id)
    assert [suite["name"] for suite in suites] == ["Login"]


def test_batch_fallback_keeps_final_test_status(listener, auth_client, robot_file):
    listener.streaming_enabled = False
    listener.start_suite(_suite("Suites", robot_file.parent), None)

    _run_suite(listener, _suite("Login", robot_file), _test("Valid Login", ["Open App"]), "FAIL")

    [result] = auth_client.executions.list_results(listener.execution_id)
    assert (result["status"], [step["status"] for step in result["step_results"]]) == (
        "failed", ["failed"],
    )


def _run_suite(listener: TestjamListener, suite, test, status: str) -> None:
    listener.start_suite(suite, None)
    listener.start_test(test, None)
    for keyword in test.body:
        listener.start_keyword(keyword, None)
        listener.end_keyword(keyword, _outcome(status))
    listener.end_test(test, _outcome(status))
    listener.end_suite(suite, None)


def _suite(name: str, source) -> SimpleNamespace:
    return SimpleNamespace(name=name, source=str(source), doc="")


def _test(name: str, keywords: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        name=name, doc="", tags=[], setup=None, teardown=None,
        body=[SimpleNamespace(name=keyword, type="KEYWORD") for keyword in keywords],
    )


def _outcome(status: str) -> SimpleNamespace:
    return SimpleNamespace(status=status, elapsedtime=5, message="")
