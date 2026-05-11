"""User notification preferences endpoints + service."""
from __future__ import annotations

from fastapi.testclient import TestClient

from testjam.auth.security import hash_password
from testjam.models.user import User
from tests.conftest import TestingSession


BASE = "/api/v1/users/me/notification-preferences"


def _login_token(client: TestClient, username: str, password: str = "pw") -> str:
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    ).json()["access_token"]


def _add_user(username: str) -> int:
    with TestingSession() as session:
        user = User(
            username=username,
            email=f"{username}@x.com",
            hashed_password=hash_password("pw"),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_list_lazy_creates_defaults(auth_client: TestClient):
    response = auth_client.get(BASE)
    assert response.status_code == 200
    body = response.json()
    by_type = {entry["event_type"]: entry for entry in body}

    assert by_type["execution_assigned"] == {
        "event_type": "execution_assigned", "in_app": True, "email": True,
    }
    assert by_type["execution_finished"] == {
        "event_type": "execution_finished", "in_app": True, "email": False,
    }
    assert by_type["execution_failed"] == {
        "event_type": "execution_failed", "in_app": True, "email": True,
    }


def test_list_is_stable_after_second_fetch(auth_client: TestClient):
    first = auth_client.get(BASE).json()
    second = auth_client.get(BASE).json()
    assert len(first) == len(second) == 3
    assert {entry["event_type"] for entry in first} == {entry["event_type"] for entry in second}


def test_get_single_returns_default_for_known_event(auth_client: TestClient):
    response = auth_client.get(f"{BASE}/execution_assigned")
    assert response.status_code == 200
    assert response.json() == {
        "event_type": "execution_assigned", "in_app": True, "email": True,
    }


def test_get_single_for_reserved_event_uses_fallback(auth_client: TestClient):
    response = auth_client.get(f"{BASE}/password_reset")
    assert response.status_code == 200
    assert response.json() == {
        "event_type": "password_reset", "in_app": True, "email": False,
    }


def test_get_single_rejects_unknown_event(auth_client: TestClient):
    response = auth_client.get(f"{BASE}/totally_made_up")
    assert response.status_code == 400


def test_put_updates_preference(auth_client: TestClient):
    response = auth_client.put(
        f"{BASE}/execution_failed",
        json={"in_app": False, "email": False},
    )
    assert response.status_code == 200
    assert response.json() == {
        "event_type": "execution_failed", "in_app": False, "email": False,
    }

    refreshed = auth_client.get(f"{BASE}/execution_failed").json()
    assert refreshed == {
        "event_type": "execution_failed", "in_app": False, "email": False,
    }


def test_put_creates_preference_if_missing(auth_client: TestClient):
    response = auth_client.put(
        f"{BASE}/mention_in_comment",
        json={"in_app": True, "email": True},
    )
    assert response.status_code == 200
    assert response.json()["email"] is True


def test_put_rejects_unknown_event(auth_client: TestClient):
    response = auth_client.put(
        f"{BASE}/garbage",
        json={"in_app": True, "email": True},
    )
    assert response.status_code == 400


def test_preferences_are_isolated_per_user(client: TestClient):
    _add_user("alice")
    _add_user("bob")
    alice_headers = {"Authorization": f"Bearer {_login_token(client, 'alice')}"}
    bob_headers = {"Authorization": f"Bearer {_login_token(client, 'bob')}"}

    client.put(
        f"{BASE}/execution_assigned",
        json={"in_app": False, "email": False},
        headers=alice_headers,
    )

    alice_view = client.get(f"{BASE}/execution_assigned", headers=alice_headers).json()
    bob_view = client.get(f"{BASE}/execution_assigned", headers=bob_headers).json()

    assert alice_view == {
        "event_type": "execution_assigned", "in_app": False, "email": False,
    }
    assert bob_view == {
        "event_type": "execution_assigned", "in_app": True, "email": True,
    }


def test_service_helpers_round_trip():
    from testjam.services import notification_preferences

    user_id = _add_user("carol")
    with TestingSession() as session:
        notification_preferences.set_preference(
            session, user_id, "execution_assigned", in_app=False, email=True,
        )
        assert notification_preferences.is_email_enabled(
            session, user_id, "execution_assigned",
        ) is True
        assert notification_preferences.is_in_app_enabled(
            session, user_id, "execution_assigned",
        ) is False
        assert notification_preferences.is_email_enabled(
            session, user_id, "execution_finished",
        ) is False
