"""Attachment upload size + MIME enforcement.

The shared `uploads.read_attachment` helper short-circuits oversize
uploads with 413 and rejects MIME types the victim's browser would
render inline (HTML, SVG, JS, executables) with 415. These tests
exercise both rails through every attachment endpoint so a regression
in any one handler — they're independent code paths — is caught.
"""
import io

import pytest

from testjam.core.config import settings


OVERSIZE_CAP = 64


@pytest.fixture
def small_cap(monkeypatch):
    monkeypatch.setattr(settings, "MAX_ATTACHMENT_BYTES", OVERSIZE_CAP)


@pytest.fixture
def case_id(auth_client, project_id):
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    return auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]


@pytest.fixture
def bug_id(auth_client, project_id):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/bugs", json={"title": "B"},
    ).json()["id"]


@pytest.fixture
def execution_id(auth_client, project_id):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": []},
    ).json()["id"]


@pytest.fixture
def result_id(auth_client, execution_id, project_id):
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S2"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC2", "suite_id": suite_id},
    ).json()["id"]
    result = auth_client.post(
        f"/api/v1/executions/{execution_id}/results",
        json={"test_case_id": case_id, "status": "passed"},
    )
    return result.json()["id"]


@pytest.fixture
def version_id(auth_client, project_id):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/versions", json={"name": "v1"},
    ).json()["id"]


def _upload(client, url, *, payload=b"hello", mime="text/plain", filename="note.txt"):
    return client.post(
        url,
        files={"file": (filename, io.BytesIO(payload), mime)},
    )


ATTACHMENT_ENDPOINTS = [
    ("case", "/api/v1/cases/{case_id}/attachments"),
    ("bug", "/api/v1/bugs/{bug_id}/attachments"),
    ("execution", "/api/v1/executions/{execution_id}/attachments"),
    ("result", "/api/v1/results/{result_id}/attachments"),
    ("version", "/api/v1/versions/{version_id}/attachments"),
]


@pytest.mark.parametrize("kind,url_template", ATTACHMENT_ENDPOINTS)
def test_oversize_attachment_returns_413(
    auth_client, small_cap, kind, url_template,
    case_id, bug_id, execution_id, result_id, version_id,
):
    url = url_template.format(
        case_id=case_id, bug_id=bug_id, execution_id=execution_id,
        result_id=result_id, version_id=version_id,
    )
    response = _upload(auth_client, url, payload=b"x" * (OVERSIZE_CAP + 1))

    assert response.status_code == 413


@pytest.mark.parametrize("kind,url_template", ATTACHMENT_ENDPOINTS)
def test_blocked_mime_returns_415(
    auth_client, kind, url_template,
    case_id, bug_id, execution_id, result_id, version_id,
):
    url = url_template.format(
        case_id=case_id, bug_id=bug_id, execution_id=execution_id,
        result_id=result_id, version_id=version_id,
    )
    response = _upload(
        auth_client, url,
        payload=b"<script>alert(1)</script>",
        mime="text/html",
        filename="exploit.html",
    )

    assert response.status_code == 415
    assert "text/html" in response.json()["detail"]


@pytest.mark.parametrize("kind,url_template", ATTACHMENT_ENDPOINTS)
def test_blocked_svg_returns_415(
    auth_client, kind, url_template,
    case_id, bug_id, execution_id, result_id, version_id,
):
    url = url_template.format(
        case_id=case_id, bug_id=bug_id, execution_id=execution_id,
        result_id=result_id, version_id=version_id,
    )
    response = _upload(
        auth_client, url,
        payload=b"<svg onload=alert(1)/>",
        mime="image/svg+xml",
        filename="exploit.svg",
    )

    assert response.status_code == 415


@pytest.mark.parametrize("kind,url_template", ATTACHMENT_ENDPOINTS)
def test_allowed_mime_under_cap_succeeds(
    auth_client, kind, url_template,
    case_id, bug_id, execution_id, result_id, version_id,
):
    url = url_template.format(
        case_id=case_id, bug_id=bug_id, execution_id=execution_id,
        result_id=result_id, version_id=version_id,
    )
    response = _upload(auth_client, url, payload=b"hello", mime="text/plain")

    assert response.status_code == 201
