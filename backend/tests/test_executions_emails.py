"""End-to-end email dispatch when a failing execution completes."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from testjam.services import notification_preferences
from tests.conftest import TestingSession


@pytest.fixture
def smtp_configured(auth_client):
    admin_id = _seed_user("root", is_admin=True)
    admin_token = _login(auth_client, "root")
    auth_client.put(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_from": "noreply@example.com",
        },
    )
    return admin_id


@pytest.fixture
def captured_emails(monkeypatch):
    captured: list[dict] = []

    def fake_send_email(_settings, to, subject, html, text=None):
        captured.append({"to": to, "subject": subject, "html": html, "text": text})
        return True

    monkeypatch.setattr(
        "testjam.services.notifications.send_email", fake_send_email,
    )
    return captured


@pytest.fixture
def execution_with_failed_result(auth_client, project_id, smtp_configured, captured_emails):
    assignee_id = _seed_user("bob", email="bob@example.com")
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    execution_id = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Sprint", "type": "manual",
            "test_case_ids": [case_id], "assigned_to_id": assignee_id,
        },
    ).json()["id"]
    auth_client.post(
        f"/api/v1/executions/{execution_id}/results",
        json={"test_case_id": case_id, "status": "failed"},
    )
    captured_emails.clear()
    return execution_id, assignee_id


def _seed_user(username, *, email=None, is_admin=False):
    with TestingSession() as session:
        user = User(
            username=username,
            email=email or f"{username}@example.com",
            hashed_password=hash_password("pw"),
            is_active=True,
            is_admin=is_admin,
        )
        session.add(user)
        session.commit()
        return user.id


def _login(client, username, password="pw"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    ).json()["access_token"]


def _complete(client, execution_id):
    client.put(
        f"/api/v1/executions/{execution_id}",
        json={"status": "completed"},
    )


def _recipients(captured):
    return sorted(item["to"] for item in captured)


def test_completion_with_failures_emails_creator_and_assignee(
    auth_client, captured_emails, execution_with_failed_result,
):
    execution_id, _assignee_id = execution_with_failed_result

    _complete(auth_client, execution_id)

    assert _recipients(captured_emails) == ["bob@example.com", "u@x.com"]
    assert all("Failed tests" in item["subject"] for item in captured_emails)


def test_completion_without_failures_does_not_email_anyone(
    auth_client, project_id, smtp_configured, captured_emails,
):
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]
    execution_id = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Clean", "type": "manual", "test_case_ids": [case_id]},
    ).json()["id"]
    auth_client.post(
        f"/api/v1/executions/{execution_id}/results",
        json={"test_case_id": case_id, "status": "passed"},
    )

    _complete(auth_client, execution_id)

    assert captured_emails == []


def test_completion_skips_email_when_user_disabled_failed_pref(
    auth_client, captured_emails, execution_with_failed_result,
):
    execution_id, assignee_id = execution_with_failed_result
    creator_id = auth_client.get("/api/v1/users/me").json()["id"]
    with TestingSession() as session:
        notification_preferences.set_preference(
            session, creator_id, "execution_failed", in_app=True, email=False,
        )

    _complete(auth_client, execution_id)

    assert _recipients(captured_emails) == ["bob@example.com"]


def test_assignment_email_dispatches_to_assignee(
    auth_client, project_id, smtp_configured, captured_emails,
):
    assignee_id = _seed_user("bob", email="bob@example.com")
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]

    auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Sprint", "type": "manual",
            "test_case_ids": [case_id], "assigned_to_id": assignee_id,
        },
    )

    assert _recipients(captured_emails) == ["bob@example.com"]
    assert "assigned to" in captured_emails[0]["subject"]


def test_assignment_to_self_does_not_email(
    auth_client, project_id, smtp_configured, captured_emails,
):
    me_id = auth_client.get("/api/v1/users/me").json()["id"]
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "TC", "suite_id": suite_id},
    ).json()["id"]

    auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Sprint", "type": "manual",
            "test_case_ids": [case_id], "assigned_to_id": me_id,
        },
    )

    assert captured_emails == []
