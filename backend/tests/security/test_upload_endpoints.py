"""End-to-end checks that every upload endpoint actually wires the
sanitization helpers. A unit-tested ``safe_filename`` is useless if a
handler forgets to call it; these tests POST a malicious filename and
assert the persisted artifact stays inside the upload root with a clean
stored name.
"""
import io

import pytest

TRAVERSAL_FILENAME = "../../etc/passwd"
EXPECTED_STORED = "passwd"


@pytest.fixture
def case_id_with_attachment_support(auth_client, project_id):
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
def version_id(auth_client, project_id):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/versions", json={"name": "v1"},
    ).json()["id"]


def _upload(auth_client, url):
    return auth_client.post(
        url,
        files={"file": (TRAVERSAL_FILENAME, io.BytesIO(b"payload"), "text/plain")},
    )


def test_execution_attachment_strips_traversal(auth_client, execution_id):
    response = _upload(auth_client, f"/api/v1/executions/{execution_id}/attachments")

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == EXPECTED_STORED


def test_case_attachment_strips_traversal(auth_client, case_id_with_attachment_support):
    response = _upload(
        auth_client, f"/api/v1/cases/{case_id_with_attachment_support}/attachments",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == EXPECTED_STORED


def test_bug_attachment_strips_traversal(auth_client, bug_id):
    response = _upload(auth_client, f"/api/v1/bugs/{bug_id}/attachments")

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == EXPECTED_STORED


def test_version_attachment_strips_traversal(auth_client, version_id):
    response = _upload(auth_client, f"/api/v1/versions/{version_id}/attachments")

    assert response.status_code == 201
    assert response.json()["filename"] == EXPECTED_STORED
