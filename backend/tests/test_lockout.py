"""Account lockout after repeated failed login attempts."""
from datetime import datetime, timedelta, timezone

import pytest

from testjam.auth.lockout import LOCKOUT_DURATION_MINUTES, MAX_FAILED_LOGINS
from testjam.auth.security import hash_password
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def user_factory():
    def _create(username: str = "alice", password: str = "correct-pw") -> User:
        with TestingSession() as db:
            user = User(
                username=username,
                email=f"{username}@x.com",
                hashed_password=hash_password(password),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    return _create


def _attempt_login(client, username: str, password: str):
    return client.post("/api/v1/auth/login", data={"username": username, "password": password})


def _read_user(user_id: int) -> User:
    with TestingSession() as db:
        return db.get(User, user_id)


def test_failed_attempts_below_threshold_do_not_lock(client, user_factory):
    user = user_factory()

    for _ in range(MAX_FAILED_LOGINS - 1):
        assert _attempt_login(client, user.username, "wrong").status_code == 401

    refreshed = _read_user(user.id)
    assert refreshed.failed_login_count == MAX_FAILED_LOGINS - 1
    assert refreshed.locked_until is None


def test_reaching_threshold_locks_account(client, user_factory):
    user = user_factory()

    for _ in range(MAX_FAILED_LOGINS):
        _attempt_login(client, user.username, "wrong")

    refreshed = _read_user(user.id)
    assert refreshed.locked_until is not None
    assert refreshed.failed_login_count == 0


def test_login_during_lockout_returns_423_with_retry_after(client, user_factory):
    user = user_factory()
    for _ in range(MAX_FAILED_LOGINS):
        _attempt_login(client, user.username, "wrong")

    response = _attempt_login(client, user.username, "correct-pw")

    assert response.status_code == 423
    assert int(response.headers["Retry-After"]) > 0


def test_successful_login_clears_failed_count(client, user_factory):
    user = user_factory()
    for _ in range(MAX_FAILED_LOGINS - 1):
        _attempt_login(client, user.username, "wrong")

    response = _attempt_login(client, user.username, "correct-pw")

    assert response.status_code == 200
    assert _read_user(user.id).failed_login_count == 0


def test_login_after_lockout_expiration_succeeds(client, user_factory):
    user = user_factory()
    with TestingSession() as db:
        target = db.get(User, user.id)
        target.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        target.failed_login_count = 0
        db.commit()

    response = _attempt_login(client, user.username, "correct-pw")

    assert response.status_code == 200
    refreshed = _read_user(user.id)
    assert refreshed.locked_until is None


def test_unknown_username_does_not_persist_state(client):
    response = _attempt_login(client, "ghost", "anything")

    assert response.status_code == 401
    with TestingSession() as db:
        assert db.query(User).filter(User.username == "ghost").first() is None


def test_lockout_duration_constant_is_positive():
    assert LOCKOUT_DURATION_MINUTES > 0
    assert MAX_FAILED_LOGINS > 0
