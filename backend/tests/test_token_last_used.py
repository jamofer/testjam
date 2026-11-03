from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from testjam.auth.dependencies import TOKEN_LAST_USED_RESOLUTION
from testjam.main import app
from testjam.models.token import ApiToken
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def token(auth_client):
    created = auth_client.post("/api/v1/users/me/tokens", json={"name": "ci"}).json()
    return {"id": created["id"], "raw": created["token"]}


@pytest.fixture
def recent_use():
    return datetime.now(UTC) - TOKEN_LAST_USED_RESOLUTION / 2


@pytest.fixture
def stale_use():
    return datetime.now(UTC) - TOKEN_LAST_USED_RESOLUTION * 2


@pytest.fixture
def token_client(token):
    client = TestClient(app)
    client.headers["X-API-Key"] = token["raw"]
    return client


def test_first_use_records_last_used_at(token, token_client):
    token_client.get("/api/v1/users/me")

    assert _last_used_at(token["id"]) is not None


def test_use_within_resolution_does_not_write(token, token_client, recent_use):
    _set_last_used_at(token["id"], recent_use)

    token_client.get("/api/v1/users/me")

    assert _last_used_at(token["id"]) == recent_use


def test_use_after_resolution_refreshes_last_used_at(token, token_client, stale_use, recent_use):
    _set_last_used_at(token["id"], stale_use)

    token_client.get("/api/v1/users/me")

    assert _last_used_at(token["id"]) > recent_use


def test_rejected_token_does_not_record_use(token, token_client):
    _deactivate_token_owner(token["id"])

    response = token_client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert _last_used_at(token["id"]) is None


def _last_used_at(token_id: int) -> datetime | None:
    with TestingSession() as db:
        return db.get(ApiToken, token_id).last_used_at


def _set_last_used_at(token_id: int, moment: datetime) -> None:
    with TestingSession() as db:
        db.get(ApiToken, token_id).last_used_at = moment
        db.commit()


def _deactivate_token_owner(token_id: int) -> None:
    with TestingSession() as db:
        db.get(User, db.get(ApiToken, token_id).user_id).is_active = False
        db.commit()
