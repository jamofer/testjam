import os

import pytest

from testjam.models.bug import BugAttachment
from testjam.models.execution import ExecutionAttachment, ResultAttachment
from testjam.models.testcase import Attachment
from testjam.models.version import VersionAttachment
from tests.conftest import TestingSession

UPLOAD = {"file": ("evidence.txt", b"evidence", "text/plain")}


@pytest.fixture
def case_file(auth_client, case_ids):
    attachment_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/attachments", files=UPLOAD).json()["id"]
    return _stored_path(Attachment, attachment_id)


@pytest.fixture
def execution_id(auth_client, project_id, case_ids):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": case_ids[:1]},
    ).json()["id"]


@pytest.fixture
def project_files(auth_client, project_id, execution_id):
    bug_id = auth_client.post(f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"}).json()["id"]
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "v1"}).json()["id"]
    result_id = auth_client.get(f"/api/v1/executions/{execution_id}/results").json()[0]["id"]
    uploads = [
        (BugAttachment, f"/api/v1/bugs/{bug_id}/attachments"),
        (VersionAttachment, f"/api/v1/versions/{version_id}/attachments"),
        (ExecutionAttachment, f"/api/v1/executions/{execution_id}/attachments"),
        (ResultAttachment, f"/api/v1/results/{result_id}/attachments"),
    ]
    return [
        _stored_path(model, auth_client.post(url, files=UPLOAD).json()["id"])
        for model, url in uploads
    ]


def test_deleting_attachment_removes_its_file(auth_client, case_ids, case_file):
    attachment_id = auth_client.get(f"/api/v1/cases/{case_ids[0]}/attachments").json()[0]["id"]

    auth_client.delete(f"/api/v1/cases/{case_ids[0]}/attachments/{attachment_id}")

    assert not os.path.exists(case_file)


def test_bulk_deleting_cases_removes_their_files(auth_client, case_ids, case_file):
    response = auth_client.post("/api/v1/cases/bulk-delete", json={"ids": case_ids})

    assert response.json() == {"deleted": len(case_ids)}
    assert not os.path.exists(case_file)


def test_deleting_suite_removes_files_of_its_cases(auth_client, suite_id, case_file):
    auth_client.delete(f"/api/v1/suites/{suite_id}")

    assert not os.path.exists(case_file)


def test_deleting_execution_removes_its_files(auth_client, execution_id, project_files):
    execution_files = project_files[2:]

    auth_client.delete(f"/api/v1/executions/{execution_id}")

    assert [os.path.exists(path) for path in execution_files] == [False, False]


def test_deleting_project_removes_every_file(auth_client, project_id, case_file, project_files):
    auth_client.delete(f"/api/v1/projects/{project_id}")

    assert [os.path.exists(path) for path in [case_file, *project_files]] == [False] * 5


def test_rolled_back_delete_keeps_the_file(case_file):
    with TestingSession() as db:
        db.delete(db.query(Attachment).one())
        db.flush()

        db.rollback()

    assert os.path.exists(case_file)


def _stored_path(model, attachment_id: int) -> str:
    with TestingSession() as db:
        return db.get(model, attachment_id).file_path
