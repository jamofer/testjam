"""Step rows of the execution HTML report stay compact and readable on phones."""
import pytest

FAILED_STEP_ACTION = "Submit the form"
TEARDOWN_STEP_ACTION = "Close the browser"


@pytest.fixture
def report_html(auth_client, project_id, case_ids):
    failed_step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": FAILED_STEP_ACTION, "order": 1,
    }).json()["id"]
    teardown_step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": TEARDOWN_STEP_ACTION, "order": 2, "step_type": "teardown",
    }).json()["id"]
    execution_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Stepped run", "type": "automatic", "test_case_ids": case_ids,
    }).json()["id"]
    auth_client.post(f"/api/v1/executions/{execution_id}/results", json={
        "test_case_id": case_ids[0],
        "status": "failed",
        "step_results": [
            {"step_id": failed_step_id, "status": "failed", "duration_ms": 23},
            {"step_id": teardown_step_id, "status": "passed", "duration_ms": 295},
        ],
    })
    return auth_client.get(f"/api/v1/executions/{execution_id}/export/html").text


def test_step_row_shows_its_status_as_a_glyph(report_html):
    assert '<span class="sglyph sg-failed" title="failed">✗</span>' in report_html
    assert '<span class="sglyph sg-passed" title="passed">✓</span>' in report_html


def test_step_row_shows_its_duration(report_html):
    assert '<span class="sdur">23ms</span>' in report_html


def test_action_steps_carry_no_type_label(report_html):
    assert '<span class="kpill kp-type">Action</span>' not in report_html


def test_teardown_steps_keep_their_type_label(report_html):
    assert '<span class="kpill kp-type">Teardown</span>' in report_html


def test_report_ships_phone_width_layout_rules(report_html):
    assert "@media (max-width:640px)" in report_html
