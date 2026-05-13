import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from testjam.routers.settings import RESTORE_CONFIRM_TOKEN
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


def _confirm_query():
    return {"confirm": RESTORE_CONFIRM_TOKEN}


def test_restore_requires_authentication(client: TestClient):
    resp = client.post("/api/v1/settings/restore", params=_confirm_query(),
                       files={"file": ("backup.zip", b"x", "application/zip")})

    assert resp.status_code == 401


def test_restore_rejects_non_admin(non_admin_client: TestClient):
    resp = non_admin_client.post("/api/v1/settings/restore", params=_confirm_query(),
                                 files={"file": ("backup.zip", b"x", "application/zip")})

    assert resp.status_code == 403


def test_restore_requires_confirmation_token(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/settings/restore",
        params={"confirm": "nope"},
        files={"file": ("backup.zip", b"x", "application/zip")},
    )

    assert resp.status_code == 400
    assert "confirmation" in resp.json()["detail"].lower()


def test_restore_rejects_invalid_zip(auth_client: TestClient):
    resp = auth_client.post(
        "/api/v1/settings/restore",
        params=_confirm_query(),
        files={"file": ("backup.zip", b"not a zip", "application/zip")},
    )

    assert resp.status_code == 400
    assert "zip" in resp.json()["detail"].lower()


def test_restore_rejects_missing_manifest(auth_client: TestClient):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dump.sql", "SELECT 1;")
    buf.seek(0)

    resp = auth_client.post(
        "/api/v1/settings/restore",
        params=_confirm_query(),
        files={"file": ("backup.zip", buf.read(), "application/zip")},
    )

    assert resp.status_code == 400
    assert "manifest" in resp.json()["detail"].lower()


def test_restore_rejects_dialect_mismatch(auth_client: TestClient):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", json.dumps({
            "format_version": 1, "dialect": "postgresql",
        }))
        zf.writestr("dump.sql", "SELECT 1;")
    buf.seek(0)

    resp = auth_client.post(
        "/api/v1/settings/restore",
        params=_confirm_query(),
        files={"file": ("backup.zip", buf.read(), "application/zip")},
    )

    assert resp.status_code == 400
    assert "dialect" in resp.json()["detail"].lower()


def test_backup_restore_roundtrip(auth_client: TestClient, project_id):
    backup = auth_client.get("/api/v1/settings/backup")
    assert backup.status_code == 200
    archive = backup.content

    deleted = auth_client.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 204
    assert auth_client.get(f"/api/v1/projects/{project_id}").status_code == 404

    resp = auth_client.post(
        "/api/v1/settings/restore",
        params=_confirm_query(),
        files={"file": ("backup.zip", archive, "application/zip")},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dialect"] == "sqlite"
    restored = auth_client.get(f"/api/v1/projects/{project_id}")
    assert restored.status_code == 200
    assert restored.json()["name"] == "TestProject"
