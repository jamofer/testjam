import io
import json
import zipfile

from fastapi.testclient import TestClient


def test_export_returns_zip_with_project_data(auth_client: TestClient, project_id, suite_id, case_ids):
    resp = auth_client.get(f"/api/v1/projects/{project_id}/export")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = set(zf.namelist())
        assert "manifest.json" in names
        assert "project.json" in names
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["project_id"] == project_id
        assert manifest["project_name"] == "TestProject"
        document = json.loads(zf.read("project.json"))

    assert document["project"]["id"] == project_id
    assert len(document["suites"]) == 1
    assert document["suites"][0]["id"] == suite_id
    assert {c["id"] for c in document["cases"]} == set(case_ids)


def test_export_includes_case_attachments(auth_client: TestClient, project_id, case_ids):
    case_id = case_ids[0]
    upload = auth_client.post(
        f"/api/v1/cases/{case_id}/attachments",
        files={"file": ("note.txt", b"hello world", "text/plain")},
    )
    assert upload.status_code in (200, 201), upload.text

    resp = auth_client.get(f"/api/v1/projects/{project_id}/export")

    assert resp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        archive_names = zf.namelist()
        case_attachment_paths = [n for n in archive_names if n.startswith(f"attachments/cases/{case_id}/")]
        assert case_attachment_paths
        assert zf.read(case_attachment_paths[0]) == b"hello world"


def test_export_rejects_unauthenticated(client: TestClient, project_id):
    client.headers.pop("Authorization", None)
    resp = client.get(f"/api/v1/projects/{project_id}/export")

    assert resp.status_code == 401


def test_export_unknown_project_returns_404(auth_client: TestClient):
    resp = auth_client.get("/api/v1/projects/99999/export")

    assert resp.status_code in (403, 404)
