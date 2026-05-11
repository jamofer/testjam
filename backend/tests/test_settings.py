"""AppSettings router + wiring tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from tests.conftest import TestingSession


def _add_admin() -> int:
    with TestingSession() as db:
        u = User(
            username="root", email="root@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id


def _admin_client(client: TestClient) -> TestClient:
    _add_admin()
    token = client.post("/api/v1/auth/login", data={"username": "root", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_public_settings_anon_readable(client: TestClient):
    resp = client.get("/api/v1/settings/public")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app_name"] == "Testjam"
    assert body["allow_registration"] is True
    assert "site_url" in body
    assert body["smtp_configured"] is False


def test_public_settings_reports_smtp_configured_after_admin_sets_it(client: TestClient):
    admin = _admin_client(client)
    admin.put("/api/v1/settings", json={
        "smtp_host": "smtp.example.com",
        "smtp_from": "noreply@example.com",
    })
    body = client.get("/api/v1/settings/public").json()
    assert body["smtp_configured"] is True


def test_admin_get_returns_settings_with_masked_secret(auth_client: TestClient):
    _add_admin()
    root_token = auth_client.post("/api/v1/auth/login", data={"username": "root", "password": "pw"}).json()["access_token"]
    resp = auth_client.get("/api/v1/settings", headers={"Authorization": f"Bearer {root_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["smtp_password_set"] is False
    assert "smtp_password" not in body


def test_non_admin_cannot_read_settings(auth_client: TestClient):
    resp = auth_client.get("/api/v1/settings")
    assert resp.status_code == 403


def test_admin_put_updates_and_marks_password_set(client: TestClient):
    c = _admin_client(client)
    resp = c.put("/api/v1/settings", json={
        "site_url": "https://qa.example.com",
        "app_name": "Acme QA",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_from": "qa@example.com",
        "smtp_password": "secret",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["site_url"] == "https://qa.example.com"
    assert body["app_name"] == "Acme QA"
    assert body["smtp_password_set"] is True


def test_smtp_password_clear_with_empty_string(client: TestClient):
    c = _admin_client(client)
    c.put("/api/v1/settings", json={"smtp_password": "secret"})
    c.put("/api/v1/settings", json={"smtp_password": ""})
    resp = c.get("/api/v1/settings")
    assert resp.json()["smtp_password_set"] is False


def test_html_export_uses_site_url(client: TestClient):
    c = _admin_client(client)
    c.put("/api/v1/settings", json={"site_url": "https://qa.example.com"})

    project_id = c.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    suite_id = c.post(f"/api/v1/projects/{project_id}/suites", json={"name": "S"}).json()["id"]
    case_id = c.post(f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id}).json()["id"]
    exec_id = c.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual", "test_case_ids": [case_id],
    }).json()["id"]

    resp = c.get(f"/api/v1/executions/{exec_id}/export/html")
    assert resp.status_code == 200
    assert "https://qa.example.com/executions/" in resp.text


def test_html_export_uses_app_name(client: TestClient):
    c = _admin_client(client)
    c.put("/api/v1/settings", json={"app_name": "Acme QA", "site_url": "https://qa.example.com"})

    project_id = c.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    suite_id = c.post(f"/api/v1/projects/{project_id}/suites", json={"name": "S"}).json()["id"]
    case_id = c.post(f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id}).json()["id"]
    exec_id = c.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual", "test_case_ids": [case_id],
    }).json()["id"]

    resp = c.get(f"/api/v1/executions/{exec_id}/export/html")
    assert "View in Acme QA" in resp.text
    assert "Acme QA" in resp.text
    assert "Run — Acme QA" in resp.text  # html <title>
    assert "Acme QA · 1 test" in resp.text  # footer


def test_assignment_sends_email_when_smtp_configured(auth_client: TestClient, project_id, case_ids):
    _add_admin()
    root_token = auth_client.post("/api/v1/auth/login", data={"username": "root", "password": "pw"}).json()["access_token"]
    auth_client.put("/api/v1/settings", json={
        "smtp_host": "smtp.example.com",
        "smtp_from": "noreply@example.com",
    }, headers={"Authorization": f"Bearer {root_token}"})

    with TestingSession() as db:
        bob = User(username="bob", email="bob@x.com",
                   hashed_password=hash_password("pw"), is_active=True)
        db.add(bob)
        db.commit()
        db.refresh(bob)
        bob_id = bob.id

    with patch("testjam.services.notifications.send_email") as mock_send:
        resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
            "title": "R", "type": "manual",
            "assigned_to_id": bob_id, "test_case_ids": case_ids,
        })
        assert resp.status_code == 201

    assert mock_send.called
    args, _ = mock_send.call_args
    settings_arg, to_arg, subject_arg, html_arg = args[:4]
    assert to_arg == "bob@x.com"
    assert "assigned" in subject_arg.lower()
    assert "<a href" in html_arg


def test_assignment_does_not_send_email_when_smtp_unset(auth_client: TestClient, project_id, case_ids):
    with TestingSession() as db:
        bob = User(username="bob", email="bob@x.com",
                   hashed_password=hash_password("pw"), is_active=True)
        db.add(bob)
        db.commit()
        db.refresh(bob)
        bob_id = bob.id

    with patch("testjam.services.notifications.send_email") as mock_send:
        auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
            "title": "R", "type": "manual",
            "assigned_to_id": bob_id, "test_case_ids": case_ids,
        })

    assert not mock_send.called
