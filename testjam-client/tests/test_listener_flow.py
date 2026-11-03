"""Listener event flow against the in-process backend."""
from types import SimpleNamespace

import httpx
import pytest
import robot

from testjam_client.errors import Conflict, Locked, RateLimited, raise_for_status
from testjam_client.listener import listener as listener_module
from testjam_client.listener.listener import (
    ABORT_MESSAGES,
    MAX_CONSECUTIVE_NETWORK_FAILURES,
    TestjamListener,
)
from testjam_client.listener.session_renewal import SessionRenewal

PROJECT_NAME = "Listener Flow"
REPLAYED_EVENTS = {
    "start_suite", "end_suite", "start_test", "end_test",
    "start_body_item", "end_body_item", "log_message",
}
CONTROL_STRUCTURES_TEST = """*** Test Cases ***
With Control
    Log    first
    IF    True
        Log    inside if
    END
    FOR    ${item}    IN    1    2
        Log    ${item}
    END
    Log    after loop
"""
FAILING_TEST = """*** Test Cases ***
Fails Midway
    Log    first
    Fail    boom
    FOR    ${item}    IN    1    2
        Log    ${item}
    END
    [Teardown]    No Operation
"""


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
def outage_with_status(auth_client):
    failing = FailingStatusHttp(auth_client._http)
    auth_client.wrap_http(lambda _http: failing)
    return failing


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
    listener.start_body_item(test.body[0], None)
    outage.active = False

    listener.end_body_item(test.body[0], _outcome("FAIL"))
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


def test_steps_stay_aligned_after_control_structures(listener, auth_client, tmp_path):
    [result] = _run_robot(listener, auth_client, tmp_path, CONTROL_STRUCTURES_TEST)

    assert _step_statuses(auth_client, result) == [
        ("Log", "passed"), ("[IF/ELSE ROOT]", "passed"), ("[FOR]", "passed"), ("Log", "passed"),
    ]


def test_teardown_is_recorded_on_its_own_step_after_a_failure(listener, auth_client, tmp_path):
    [result] = _run_robot(listener, auth_client, tmp_path, FAILING_TEST)

    assert _step_statuses(auth_client, result) == [
        ("Log", "passed"), ("Fail", "failed"), ("[FOR]", "not_run"), ("No Operation", "passed"),
    ]


def test_logs_of_nested_keywords_stay_on_their_step(listener, auth_client, tmp_path):
    [result] = _run_robot(listener, auth_client, tmp_path, CONTROL_STRUCTURES_TEST)

    logs = [step["log_output"] or "" for step in _ordered_steps(auth_client, result)]
    assert "inside if" in logs[1] and "after loop" in logs[3]


def test_case_created_by_a_parallel_worker_is_reused():
    cases = RacingCases(winner={"id": 7, "name": "Valid Login"})

    case = listener_module._find_or_create_case_by_external_id(
        SimpleNamespace(cases=cases), 1, "Valid Login", external_id="Login.Valid Login",
    )

    assert case["id"] == 7


def test_case_is_skipped_when_conflict_cannot_be_resolved():
    cases = RacingCases(winner=None)

    case = listener_module._find_or_create_case_by_external_id(
        SimpleNamespace(cases=cases), 1, "Valid Login", external_id="Login.Valid Login",
    )

    assert case is None


def test_server_error_while_preparing_a_test_does_not_escape(listener, outage_with_status, robot_file):
    listener.start_suite(_suite("Login", robot_file), None)
    outage_with_status.status_code = 500

    listener.start_test(_test("Valid Login", []), None)

    assert listener._test is None


def test_expired_session_is_renewed_and_the_call_repeated():
    http = ExpiringHttp()
    renewal = SessionRenewal(http, renew=http.renew)

    response = renewal.request("GET", "/projects")

    assert (response.status_code, http.renewals) == (200, 1)


def test_rejected_login_is_not_renewed():
    http = ExpiringHttp()
    renewal = SessionRenewal(http, renew=http.renew)

    response = renewal.request("POST", "/auth/login")

    assert (response.status_code, http.renewals) == (401, 0)


def test_execution_stays_completed_after_a_normal_run(listener, auth_client):
    listener.close()

    assert auth_client.executions.get(listener.execution_id)["status"] == "completed"


@pytest.mark.parametrize("message", ABORT_MESSAGES)
def test_interrupted_run_closes_the_execution_as_aborted(listener, auth_client, robot_file, message):
    test = _test("Valid Login", [])
    listener.start_suite(_suite("Login", robot_file), None)
    listener.start_test(test, None)
    listener.end_test(test, SimpleNamespace(status="FAIL", elapsedtime=5, message=message))

    listener.close()

    assert auth_client.executions.get(listener.execution_id)["status"] == "aborted"


def test_artefacts_are_uploaded_from_the_paths_robot_reports(listener, auth_client, tmp_path):
    log_file = tmp_path / "custom-dir" / "log.html"
    log_file.parent.mkdir()
    log_file.write_text("<html></html>")
    listener.log_file(str(log_file))

    listener.close()

    attachments = auth_client.request("GET", f"/executions/{listener.execution_id}/attachments").json()
    assert [attachment["filename"] for attachment in attachments] == ["log.html"]


def test_missing_artefact_does_not_break_close(listener, tmp_path):
    listener.output_file(str(tmp_path / "gone.xml"))

    listener.close()


@pytest.mark.parametrize("status_code,error", [(423, Locked), (429, RateLimited)])
def test_lock_and_rate_limit_responses_have_their_own_error(status_code, error):
    with pytest.raises(error):
        raise_for_status(httpx.Response(status_code, json={"detail": "wait"}))


def _run_robot(listener, auth_client, directory, body: str) -> list[dict]:
    path = directory / "flow.robot"
    path.write_text(body)
    recorder = RobotEventRecorder()
    robot.run(str(path), listener=recorder, output=None, log=None, report=None, console="none")
    recorder.replay_into(listener)
    return auth_client.executions.list_results(listener.execution_id)


def _ordered_steps(auth_client, result: dict) -> list[dict]:
    steps = {step["id"]: step for step in auth_client.cases.list_steps(result["test_case_id"])}
    return sorted(result["step_results"], key=lambda row: steps[row["step_id"]]["order"])


def _step_statuses(auth_client, result: dict) -> list[tuple[str, str]]:
    steps = {step["id"]: step for step in auth_client.cases.list_steps(result["test_case_id"])}
    return [(steps[row["step_id"]]["action"], row["status"]) for row in _ordered_steps(auth_client, result)]


def _run_suite(listener: TestjamListener, suite, test, status: str) -> None:
    listener.start_suite(suite, None)
    listener.start_test(test, None)
    for keyword in test.body:
        listener.start_body_item(keyword, None)
        listener.end_body_item(keyword, _outcome(status))
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


class ExpiringHttp:
    headers: dict[str, str] = {}

    def __init__(self) -> None:
        self.renewals = 0

    def renew(self) -> None:
        self.renewals += 1

    def request(self, _method: str, _url: str, **_kwargs) -> httpx.Response:
        return httpx.Response(200 if self.renewals else 401)


class FailingStatusHttp:
    def __init__(self, http) -> None:
        self._http = http
        self.status_code: int | None = None

    @property
    def headers(self):
        return self._http.headers

    def request(self, method: str, url: str, **kwargs):
        if self.status_code is None:
            return self._http.request(method, url, **kwargs)
        return httpx.Response(self.status_code, json={"detail": "unavailable"})


class RacingCases:
    """The case does not exist when looked up, but does by the time it is created."""

    def __init__(self, winner: dict | None) -> None:
        self._winner = winner
        self._lost_race = False

    def list(self, *_args, **_kwargs) -> list[dict]:
        if self._lost_race and self._winner:
            return [self._winner]
        return []

    def create(self, *_args, **_kwargs) -> dict:
        self._lost_race = True
        raise Conflict(409, "already exists", None)


class RobotEventRecorder:
    """Captures real Robot events to replay once Robot has finished.

    The in-process API answers from another thread, which deadlocks against the
    logging lock Robot holds while it dispatches listener calls.
    """

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self) -> None:
        self._events: list[tuple[str, tuple]] = []

    def __getattr__(self, name: str):
        if name not in REPLAYED_EVENTS:
            raise AttributeError(name)
        return lambda *arguments: self._events.append((name, arguments))

    def replay_into(self, listener: TestjamListener) -> None:
        for name, arguments in self._events:
            getattr(listener, name)(*arguments)

