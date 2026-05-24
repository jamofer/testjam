"""`MAX_EXPORT_RESULTS` must short-circuit exports before the workbook or
HTML report is materialized — otherwise a 1000-result execution still
buffers megabytes of inline base64 attachments before the cap fires.

These tests monkeypatch the cap down to a tiny number so the suite stays
fast, then exercise all three export endpoints.
"""
import io

import openpyxl
import pytest

from testjam.core.config import settings
from testjam.models.execution import TestExecution, TestResult
from testjam.models.testcase import TestCase, TestSuite
from tests.conftest import TestingSession

CAP = 3


@pytest.fixture
def low_cap(monkeypatch):
    monkeypatch.setattr(settings, "MAX_EXPORT_RESULTS", CAP)


def _seed_execution_with_results(project_id, suite_id, result_count):
    with TestingSession() as db:
        execution = TestExecution(
            project_id=project_id, title="Big run", type="manual", status="completed",
        )
        db.add(execution)
        db.flush()
        for index in range(result_count):
            case = TestCase(suite_id=suite_id, name=f"TC-{index}", order=index + 1)
            db.add(case)
            db.flush()
            db.add(TestResult(
                execution_id=execution.id, test_case_id=case.id, status="passed",
            ))
        db.commit()
        return execution.id


def test_xlsx_export_returns_413_above_cap(auth_client, project_id, suite_id, low_cap):
    execution_id = _seed_execution_with_results(project_id, suite_id, CAP + 1)

    response = auth_client.get(f"/api/v1/executions/{execution_id}/export/xlsx")

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]


def test_xlsx_export_succeeds_at_cap(auth_client, project_id, suite_id, low_cap):
    execution_id = _seed_execution_with_results(project_id, suite_id, CAP)

    response = auth_client.get(f"/api/v1/executions/{execution_id}/export/xlsx")

    assert response.status_code == 200
    workbook = openpyxl.load_workbook(io.BytesIO(response.content))
    results_sheet = workbook["Results"]
    data_rows = list(results_sheet.iter_rows(min_row=2, values_only=True))
    assert len(data_rows) == CAP


def test_html_export_returns_413_above_cap(auth_client, project_id, suite_id, low_cap):
    execution_id = _seed_execution_with_results(project_id, suite_id, CAP + 1)

    response = auth_client.get(f"/api/v1/executions/{execution_id}/export/html")

    assert response.status_code == 413


def test_cases_xlsx_export_returns_413_above_cap(auth_client, project_id, suite_id, low_cap):
    with TestingSession() as db:
        for index in range(CAP + 1):
            db.add(TestCase(suite_id=suite_id, name=f"OverCap-{index}", order=index + 1))
        db.commit()

    response = auth_client.get(f"/api/v1/projects/{project_id}/cases/export/xlsx")

    assert response.status_code == 413


def test_xlsx_export_streams_in_chunks(auth_client, project_id, suite_id, low_cap, monkeypatch):
    """Even at-cap exports must come back via the chunk generator; without
    chunking the response body would be the BytesIO blob in one piece.
    """
    monkeypatch.setattr(settings, "EXPORT_STREAM_CHUNK_BYTES", 1024)
    execution_id = _seed_execution_with_results(project_id, suite_id, CAP)

    with auth_client.stream(
        "GET", f"/api/v1/executions/{execution_id}/export/xlsx",
    ) as response:
        assert response.status_code == 200
        chunks = list(response.iter_bytes())

    assert len(chunks) >= 1
    body = b"".join(chunks)
    assert body.startswith(b"PK")
