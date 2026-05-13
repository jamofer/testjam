"""API token expiration, rotation, and purge."""
from datetime import datetime, timedelta, timezone

import pytest

from testjam.models.token import ApiToken
from testjam.services.token_purge import purge_expired_tokens
from tests.conftest import TestingSession


@pytest.fixture
def project_id(admin_client):
    return admin_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]


_token_counter = 0


def _create_user_token(client, expires_at: datetime | None = None) -> dict:
    global _token_counter
    _token_counter += 1
    body = {"name": f"T-{_token_counter}"}
    if expires_at is not None:
        body["expires_at"] = expires_at.isoformat()
    return client.post("/api/v1/users/me/tokens", json=body).json()


def _set_token_expiration(token_id: int, expires_at: datetime) -> None:
    with TestingSession() as db:
        token = db.get(ApiToken, token_id)
        token.expires_at = expires_at
        db.commit()


def test_create_user_token_persists_expires_at(admin_client):
    expires_at = datetime(2030, 1, 1, 12, 0, 0)

    created = _create_user_token(admin_client, expires_at=expires_at)

    assert created["expires_at"].startswith("2030-01-01T12:00:00")


def test_create_user_token_without_expiration_returns_null(admin_client):
    created = _create_user_token(admin_client)

    assert created["expires_at"] is None


def test_expired_token_cannot_authenticate(admin_client):
    created = _create_user_token(admin_client)
    _set_token_expiration(created["id"], datetime.now(timezone.utc) - timedelta(seconds=1))

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = created["token"]

    assert admin_client.get("/api/v1/users/me").status_code == 401


def test_token_with_future_expiration_authenticates(admin_client):
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    created = _create_user_token(admin_client, expires_at=future)

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = created["token"]

    assert admin_client.get("/api/v1/users/me").status_code == 200


def test_rotate_user_token_invalidates_old_and_returns_new(admin_client):
    created = _create_user_token(admin_client)
    old_raw = created["token"]

    rotated = admin_client.post(f"/api/v1/users/me/tokens/{created['id']}/rotate").json()
    new_raw = rotated["token"]

    assert new_raw != old_raw
    assert rotated["id"] == created["id"]

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = old_raw
    assert admin_client.get("/api/v1/users/me").status_code == 401

    admin_client.headers["X-API-Key"] = new_raw
    assert admin_client.get("/api/v1/users/me").status_code == 200


def test_rotate_user_token_clears_last_used_at(admin_client):
    created = _create_user_token(admin_client)
    admin_client.headers["X-API-Key"] = created["token"]
    admin_client.get("/api/v1/users/me")
    admin_client.headers.pop("X-API-Key")

    admin_client.post(f"/api/v1/users/me/tokens/{created['id']}/rotate")

    listed = admin_client.get("/api/v1/users/me/tokens").json()
    assert listed[0]["last_used_at"] is None


def test_rotate_unknown_token_returns_404(admin_client):
    response = admin_client.post("/api/v1/users/me/tokens/9999/rotate")

    assert response.status_code == 404


def test_rotate_project_token_invalidates_old(admin_client, project_id):
    created = admin_client.post(
        f"/api/v1/projects/{project_id}/tokens", json={"name": "ci"},
    ).json()
    old_raw = created["token"]

    rotated = admin_client.post(
        f"/api/v1/projects/{project_id}/tokens/{created['id']}/rotate",
    ).json()

    assert rotated["token"] != old_raw

    del admin_client.headers["Authorization"]
    admin_client.headers["X-API-Key"] = old_raw
    assert admin_client.get("/api/v1/users/me").status_code == 401


def test_purge_expired_tokens_deletes_only_expired_rows(admin_client):
    expired_id = _create_user_token(admin_client)["id"]
    fresh_id = _create_user_token(
        admin_client, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )["id"]
    never_expires_id = _create_user_token(admin_client)["id"]
    _set_token_expiration(expired_id, datetime.now(timezone.utc) - timedelta(minutes=1))

    with TestingSession() as db:
        deleted = purge_expired_tokens(db)

    assert deleted == 1
    with TestingSession() as db:
        remaining = {token.id for token in db.query(ApiToken).all()}
    assert remaining == {fresh_id, never_expires_id}


def test_purge_dry_run_does_not_delete(admin_client):
    expired_id = _create_user_token(admin_client)["id"]
    _set_token_expiration(expired_id, datetime.now(timezone.utc) - timedelta(minutes=1))

    with TestingSession() as db:
        counted = purge_expired_tokens(db, dry_run=True)

    assert counted == 1
    with TestingSession() as db:
        assert db.query(ApiToken).count() == 1
