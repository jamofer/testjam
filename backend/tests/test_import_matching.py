import pytest

JUNIT_FAILURE = b"""<?xml version="1.0"?>
<testsuite name="pytest">
  <testcase classname="tests.checkout" name="Pay by card">
    <failure message="AssertionError: expected 200 got 500">Traceback (most recent call last):
  File "tests/checkout.py", line 12, in test_pay
AssertionError: expected 200 got 500</failure>
  </testcase>
</testsuite>"""

JUNIT_BY_NAME = b"""<?xml version="1.0"?>
<testsuite name="pytest">
  <testcase name="Pay by card"><failure message="boom"/></testcase>
</testsuite>"""

JUNIT_BY_EXTERNAL_ID = b"""<?xml version="1.0"?>
<testsuite name="pytest">
  <testcase classname="tests.checkout" name="pay_eu"><failure message="boom"/></testcase>
</testsuite>"""

RF_BY_NAME = b"""<?xml version="1.0" encoding="UTF-8"?>
<robot generator="Robot 7">
  <suite name="Checkout">
    <test name="Pay by card"><status status="FAIL">boom</status></test>
  </suite>
</robot>"""


@pytest.fixture
def other_suite_id(auth_client, project_id):
    return auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "EU"}).json()["id"]


@pytest.fixture
def card_case_id(auth_client, suite_id):
    return _create_case(auth_client, suite_id, "Pay by card")


@pytest.fixture
def twin_case_ids(auth_client, suite_id, other_suite_id):
    return [
        _create_case(auth_client, suite_id, "Pay by card", external_id="tests.checkout.pay_us"),
        _create_case(auth_client, other_suite_id, "Pay by card", external_id="tests.checkout.pay_eu"),
    ]


def test_junit_failure_keeps_the_stack_trace(auth_client, project_id, card_case_id):
    execution_id = _create_execution(auth_client, project_id, [card_case_id])

    _import(auth_client, execution_id, "junit", JUNIT_FAILURE)

    comment = _results(auth_client, execution_id)[0]["comment"]
    assert comment.startswith("AssertionError: expected 200 got 500")
    assert 'File "tests/checkout.py", line 12' in comment


def test_junit_entry_matching_several_cases_is_reported(auth_client, project_id, twin_case_ids):
    execution_id = _create_execution(auth_client, project_id, twin_case_ids)

    body = _import(auth_client, execution_id, "junit", JUNIT_BY_NAME)

    assert body["errors"][0]["error"].startswith("Several test cases share this name")
    assert [result["status"] for result in _results(auth_client, execution_id)] == ["not_run", "not_run"]


def test_external_id_tells_cases_with_the_same_name_apart(auth_client, project_id, twin_case_ids):
    execution_id = _create_execution(auth_client, project_id, twin_case_ids)

    _import(auth_client, execution_id, "junit", JUNIT_BY_EXTERNAL_ID)

    statuses = {result["test_case_id"]: result["status"] for result in _results(auth_client, execution_id)}
    assert statuses == {twin_case_ids[0]: "not_run", twin_case_ids[1]: "failed"}


def test_robot_entry_matching_several_cases_is_reported(auth_client, project_id, twin_case_ids):
    execution_id = _create_execution(auth_client, project_id, twin_case_ids)

    body = _import(auth_client, execution_id, "robotframework", RF_BY_NAME)

    assert body["errors"][0]["error"].startswith("Several test cases share this name")


def _create_case(client, suite_id: int, name: str, external_id: str | None = None) -> int:
    payload = {"name": name, "suite_id": suite_id, "external_id": external_id}
    return client.post(f"/api/v1/suites/{suite_id}/cases", json=payload).json()["id"]


def _create_execution(client, project_id: int, case_ids: list[int]) -> int:
    return client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "CI", "type": "automatic", "test_case_ids": case_ids},
    ).json()["id"]


def _import(client, execution_id: int, kind: str, report: bytes) -> dict:
    return client.post(
        f"/api/v1/executions/{execution_id}/results/import/{kind}",
        files={"file": ("report.xml", report, "application/xml")},
    ).json()


def _results(client, execution_id: int) -> list[dict]:
    return client.get(f"/api/v1/executions/{execution_id}/results").json()
