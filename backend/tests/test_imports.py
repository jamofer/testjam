import io


JUNIT_SIMPLE = b"""<?xml version="1.0"?>
<testsuite name="pytest" tests="3">
  <testcase classname="tests.login" name="test_login_ok" time="0.5"/>
  <testcase classname="tests.login" name="test_login_fail" time="0.3">
    <failure message="AssertionError: expected 200 got 401">stack trace</failure>
  </testcase>
  <testcase classname="tests.login" name="test_session_expired" time="0.1">
    <skipped message="not implemented"/>
  </testcase>
</testsuite>"""

RF_OUTPUT = b"""<?xml version="1.0" encoding="UTF-8"?>
<robot generator="Robot 7" rpa="false" schemaversion="5">
  <suite name="Login">
    <test name="Valid Login" id="s1-t1">
      <kw name="Open Browser" type="setup">
        <msg timestamp="20240101 12:00:00.100" level="INFO">Opening Chrome</msg>
        <status status="PASS" starttime="20240101 12:00:00.000" endtime="20240101 12:00:01.000"/>
      </kw>
      <kw name="Input Credentials">
        <msg timestamp="20240101 12:00:01.100" level="INFO">Entering admin/pass</msg>
        <status status="PASS" starttime="20240101 12:00:01.000" endtime="20240101 12:00:01.500"/>
      </kw>
      <status status="PASS" starttime="20240101 12:00:00.000" endtime="20240101 12:00:02.000"/>
    </test>
    <test name="Invalid Password" id="s1-t2">
      <kw name="Input Wrong Credentials">
        <status status="FAIL" starttime="20240101 12:00:02.000" endtime="20240101 12:00:02.500"/>
      </kw>
      <status status="FAIL" starttime="20240101 12:00:02.000" endtime="20240101 12:00:03.000">
        Login page still shown
      </status>
    </test>
    <status status="FAIL"/>
  </suite>
</robot>"""


def _setup_cases_with_external_ids(auth_client, project_id, suite_id):
    cases = [
        {"name": "Login OK", "suite_id": suite_id, "external_id": "tests.login.test_login_ok"},
        {"name": "Login Fail", "suite_id": suite_id, "external_id": "tests.login.test_login_fail"},
        {"name": "Session Expired", "suite_id": suite_id, "external_id": "tests.login.test_session_expired"},
    ]
    ids = []
    for c in cases:
        ids.append(auth_client.post(f"/api/v1/suites/{suite_id}/cases", json=c).json()["id"])
    return ids


def _create_execution(auth_client, project_id, case_ids):
    return auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "CI Run", "type": "automatic", "test_case_ids": case_ids,
    }).json()["id"]


# ─── JUnit ────────────────────────────────────────────────────────────────────

def test_junit_import_matches_by_external_id(auth_client, project_id, suite_id):
    case_ids = _setup_cases_with_external_ids(auth_client, project_id, suite_id)
    exec_id = _create_execution(auth_client, project_id, case_ids)

    resp = auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/junit",
        files={"file": ("junit.xml", io.BytesIO(JUNIT_SIMPLE), "application/xml")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["errors"] == []
    assert data["created"] + data["updated"] == 3


def test_junit_import_sets_correct_statuses(auth_client, project_id, suite_id):
    case_ids = _setup_cases_with_external_ids(auth_client, project_id, suite_id)
    exec_id = _create_execution(auth_client, project_id, case_ids)
    auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/junit",
        files={"file": ("junit.xml", io.BytesIO(JUNIT_SIMPLE), "application/xml")},
    )

    results = auth_client.get(f"/api/v1/executions/{exec_id}/results").json()
    statuses = {r["test_case_title"]: r["status"] for r in results}

    assert statuses["Login OK"] == "passed"
    assert statuses["Login Fail"] == "failed"
    assert statuses["Session Expired"] == "blocked"


def test_junit_import_unmatched_case_reported_as_error(auth_client, project_id, suite_id, case_ids):
    exec_id = _create_execution(auth_client, project_id, case_ids)
    junit_xml = b"""<testsuite><testcase classname="x" name="nonexistent_test"/></testsuite>"""

    resp = auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/junit",
        files={"file": ("junit.xml", io.BytesIO(junit_xml), "application/xml")},
    )

    assert resp.status_code == 200
    assert len(resp.json()["errors"]) == 1


def test_junit_import_invalid_xml_returns_400(auth_client, project_id, case_ids):
    exec_id = _create_execution(auth_client, project_id, case_ids)

    resp = auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/junit",
        files={"file": ("bad.xml", io.BytesIO(b"not xml at all"), "application/xml")},
    )

    assert resp.status_code == 400


# ─── Robot Framework ──────────────────────────────────────────────────────────

def _setup_rf_cases(auth_client, project_id, suite_id):
    cases = [
        {"name": "Valid Login", "suite_id": suite_id, "external_id": "login.valid login"},
        {"name": "Invalid Password", "suite_id": suite_id, "external_id": "login.invalid password"},
    ]
    ids = []
    for c in cases:
        ids.append(auth_client.post(f"/api/v1/suites/{suite_id}/cases", json=c).json()["id"])
    return ids


def test_rf_import_sets_pass_fail_statuses(auth_client, project_id, suite_id):
    case_ids = _setup_rf_cases(auth_client, project_id, suite_id)
    exec_id = _create_execution(auth_client, project_id, case_ids)

    resp = auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/robotframework",
        files={"file": ("output.xml", io.BytesIO(RF_OUTPUT), "application/xml")},
    )

    assert resp.status_code == 200
    assert resp.json()["errors"] == []

    results = auth_client.get(f"/api/v1/executions/{exec_id}/results").json()
    statuses = {r["test_case_title"]: r["status"] for r in results}
    assert statuses["Valid Login"] == "passed"
    assert statuses["Invalid Password"] == "failed"


def test_rf_import_populates_step_log_output(auth_client, project_id, suite_id):
    case_ids = _setup_rf_cases(auth_client, project_id, suite_id)
    step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Open Browser", "order": 1, "step_type": "setup",
    }).json()["id"]
    exec_id = _create_execution(auth_client, project_id, case_ids)
    auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/robotframework",
        files={"file": ("output.xml", io.BytesIO(RF_OUTPUT), "application/xml")},
    )

    result = next(
        r for r in auth_client.get(f"/api/v1/executions/{exec_id}/results").json()
        if r["test_case_title"] == "Valid Login"
    )
    result_detail = auth_client.get(f"/api/v1/results/{result['id']}").json()

    sr = next((s for s in result_detail["step_results"] if s["step_id"] == step_id), None)
    assert sr is not None
    assert "Opening Chrome" in (sr["log_output"] or "")


def test_rf_import_invalid_xml_returns_400(auth_client, project_id, case_ids):
    exec_id = _create_execution(auth_client, project_id, case_ids)

    resp = auth_client.post(
        f"/api/v1/executions/{exec_id}/results/import/robotframework",
        files={"file": ("output.xml", io.BytesIO(b"garbage"), "application/xml")},
    )

    assert resp.status_code == 400
