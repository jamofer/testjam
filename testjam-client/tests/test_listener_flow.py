"""Listener event flow against the in-process backend."""
from types import SimpleNamespace

import httpx
import pytest

from testjam_client.listener import listener as listener_module
from testjam_client.listener.listener import MAX_CONSECUTIVE_NETWORK_FAILURES, TestjamListener

PROJECT_NAME = "Listener Flow"


@pytest.fixture
def listener(auth_client, monkeypatch):
    monkeypatch.setenv("TESTJAM_API_KEY", "unused-by-the-in-process-client")
    monkeypatch.setenv("TESTJAM_PROJECT", PROJECT_NAME)
    monkeypatch.setattr(listener_module, "TestjamClient", lambda *args, **kwargs: auth_client)
    return TestjamListener()


@pytest.fixture
def outage(auth_client):
    interruptible = InterruptibleHttp(auth_client._http)
    auth_client.wrap_http(lambda _http: interruptible)
    return interruptible


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


def test_outage_does_not_break_the_robot_run(outage, listener, robot_file):
    outage.active = True

    _run_suite(listener, _suite("Login", robot_file), _test("Valid Login", ["Open App"]), "PASS")

    assert listener._test is None


def test_outage_stops_calling_the_server(outage, listener, robot_file):
    outage.active = True
    outage.attempts = 0

    for name in ("First", "Second", "Third", "Fourth"):
        _run_suite(listener, _suite(name, robot_file), _test("Valid Login", ["Open App"]), "PASS")

    assert outage.attempts == MAX_CONSECUTIVE_NETWORK_FAILURES


def test_outage_on_step_start_falls_back_to_batch(outage, listener, auth_client, robot_file):
    test = _test("Valid Login", ["Open App"])
    listener.start_suite(_suite("Login", robot_file), None)
    listener.start_test(test, None)
    outage.active = True
    listener.start_keyword(test.body[0], None)
    outage.active = False

    listener.end_keyword(test.body[0], _outcome("FAIL"))
    listener.end_test(test, _outcome("FAIL"))

    [result] = auth_client.executions.list_results(listener.execution_id)
    assert (listener.streaming_enabled, [step["status"] for step in result["step_results"]]) == (
        False, ["failed"],
    )


def test_tests_of_unreachable_suite_are_not_reported_under_its_parent(
    outage, listener, auth_client, robot_file,
):
    listener.start_suite(_suite("Suites", robot_file.parent), None)
    parent = _suite("Parent", robot_file.parent)
    listener.start_suite(parent, None)
    outage.active = True
    child = _suite("Child", robot_file.parent)
    listener.start_suite(child, None)
    outage.active = False

    listener.start_test(_test("Valid Login", []), None)

    assert auth_client.executions.list_results(listener.execution_id) == []


def test_close_survives_outage(outage, listener):
    outage.active = True

    listener.close()


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


class InterruptibleHttp:
    def __init__(self, http) -> None:
        self._http = http
        self.active = False
        self.attempts = 0

    @property
    def headers(self):
        return self._http.headers

    def request(self, method: str, url: str, **kwargs):
        if self.active:
            self.attempts += 1
            raise httpx.ConnectError("connection refused")
        return self._http.request(method, url, **kwargs)
