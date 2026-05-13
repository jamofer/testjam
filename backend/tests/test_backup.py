import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def non_admin_client(client: TestClient) -> TestClient:
    with TestingSession() as db:
        db.add(User(
            username="bob", email="bob@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        ))
        db.commit()
    token = client.post("/api/v1/auth/login", data={"username": "bob", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_backup_requires_authentication(client: TestClient):
    resp = client.get("/api/v1/settings/backup")

    assert resp.status_code == 401


def test_backup_rejects_non_admin(non_admin_client: TestClient):
    resp = non_admin_client.get("/api/v1/settings/backup")

    assert resp.status_code == 403


def test_backup_returns_zip_with_manifest_and_dump(auth_client: TestClient, project_id):
    resp = auth_client.get("/api/v1/settings/backup")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = set(zf.namelist())
        assert "manifest.json" in names
        assert "dump.sql" in names
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["format_version"] == 1
        assert manifest["dialect"] == "sqlite"
        assert "schema_revision" in manifest
        dump = zf.read("dump.sql").decode("utf-8")
        assert "TestProject" in dump


def test_backup_filename_header_uses_timestamp(auth_client: TestClient):
    resp = auth_client.get("/api/v1/settings/backup")

    disposition = resp.headers.get("content-disposition", "")
    assert "testjam-backup-" in disposition
    assert disposition.endswith('.zip"')
