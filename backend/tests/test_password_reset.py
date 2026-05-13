"""Password reset request + confirm endpoints."""
from datetime import datetime, timedelta, timezone

import pytest

from testjam.auth.lockout import MAX_FAILED_LOGINS
from testjam.auth.security import hash_password, verify_password
from testjam.models.password_reset import PasswordResetToken
from testjam.models.user import User
from testjam.services import password_reset as password_reset_service
from tests.conftest import TestingSession

ORIGINAL_PASSWORD = "original-pw"
NEW_PASSWORD = "new-secret-pw"


@pytest.fixture
def captured_emails(monkeypatch):
    sent: list[dict] = []

    def fake_send_email(settings_row, to, subject, html, text):
        sent.append({"to": to, "subject": subject, "html": html, "text": text})
        return True

    monkeypatch.setattr(password_reset_service, "send_email", fake_send_email)
    return sent


@pytest.fixture
def user_factory():
    def _create(username: str = "alice", email: str = "alice@x.com", is_active: bool = True) -> User:
        with TestingSession() as db:
            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(ORIGINAL_PASSWORD),
                is_active=is_active,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    return _create


def _request_reset(client, email: str):
    return client.post("/api/v1/auth/password-reset/request", json={"email": email})


def _confirm_reset(client, token: str, new_password: str = NEW_PASSWORD):
    return client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": new_password},
    )


def _read_user(user_id: int) -> User:
    with TestingSession() as db:
        return db.get(User, user_id)


def _latest_token_for(user_id: int) -> PasswordResetToken | None:
    with TestingSession() as db:
        return (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user_id)
            .order_by(PasswordResetToken.id.desc())
            .first()
        )


def test_request_returns_204_for_existing_user(client, user_factory, captured_emails):
    user = user_factory()

    response = _request_reset(client, user.email)

    assert response.status_code == 204
    assert _latest_token_for(user.id) is not None
    assert len(captured_emails) == 1
    assert captured_emails[0]["to"] == user.email


def test_request_returns_204_for_unknown_email_without_creating_token(client, captured_emails):
    response = _request_reset(client, "ghost@nowhere.com")

    assert response.status_code == 204
    assert captured_emails == []
    with TestingSession() as db:
        assert db.query(PasswordResetToken).count() == 0


def test_request_skips_inactive_users(client, user_factory, captured_emails):
    user = user_factory(is_active=False)

    response = _request_reset(client, user.email)

    assert response.status_code == 204
    assert _latest_token_for(user.id) is None
    assert captured_emails == []


def test_email_body_contains_reset_link_with_raw_token(client, user_factory, captured_emails):
    user = user_factory()
    _request_reset(client, user.email)

    email = captured_emails[0]
    body = email["html"] + email["text"]

    assert "/reset-password?token=" in body


def test_confirm_with_valid_token_updates_password(client, user_factory, monkeypatch, captured_emails):
    user = user_factory()
    captured_token: dict[str, str] = {}

    original = password_reset_service._create_reset_token

    def capture(db, target_user):
        raw, token_hash, expires_at = original(db, target_user)
        captured_token["raw"] = raw
        return raw, token_hash, expires_at

    monkeypatch.setattr(password_reset_service, "_create_reset_token", capture)
    _request_reset(client, user.email)

    response = _confirm_reset(client, captured_token["raw"])

    assert response.status_code == 204
    refreshed = _read_user(user.id)
    assert verify_password(NEW_PASSWORD, refreshed.hashed_password)
    assert not verify_password(ORIGINAL_PASSWORD, refreshed.hashed_password)


def test_confirm_marks_token_as_used(client, user_factory, monkeypatch):
    user = user_factory()
    raw_token = _generate_real_token_for(user.id)

    _confirm_reset(client, raw_token)

    used = _latest_token_for(user.id)
    assert used.used_at is not None


def test_confirm_rejects_unknown_token(client):
    response = _confirm_reset(client, "garbage-token-value")

    assert response.status_code == 400


def test_confirm_rejects_already_used_token(client, user_factory):
    user = user_factory()
    raw_token = _generate_real_token_for(user.id)

    first = _confirm_reset(client, raw_token)
    second = _confirm_reset(client, raw_token, new_password="another-pw-123")

    assert first.status_code == 204
    assert second.status_code == 400


def test_confirm_rejects_expired_token(client, user_factory):
    user = user_factory()
    raw_token = _generate_real_token_for(user.id)
    with TestingSession() as db:
        token = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user.id)
            .first()
        )
        token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()

    response = _confirm_reset(client, raw_token)

    assert response.status_code == 400


def test_confirm_rejects_weak_password(client, user_factory):
    user = user_factory()
    raw_token = _generate_real_token_for(user.id)

    response = _confirm_reset(client, raw_token, new_password="short")

    assert response.status_code == 422


def test_confirm_clears_existing_lockout(client, user_factory):
    user = user_factory()
    with TestingSession() as db:
        target = db.get(User, user.id)
        target.failed_login_count = MAX_FAILED_LOGINS - 1
        target.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
    raw_token = _generate_real_token_for(user.id)

    _confirm_reset(client, raw_token)

    refreshed = _read_user(user.id)
    assert refreshed.locked_until is None
    assert refreshed.failed_login_count == 0


def _generate_real_token_for(user_id: int) -> str:
    raw, token_hash, expires_at = PasswordResetToken.generate()
    with TestingSession() as db:
        record = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        db.add(record)
        db.commit()
    return raw
