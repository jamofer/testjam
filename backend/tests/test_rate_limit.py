"""Login endpoint rejects after exceeding the per-IP rate limit."""
import pytest

from testjam.core.rate_limit import LOGIN_RATE_LIMIT, limiter
from testjam.models.settings import AppSettings
from tests.conftest import TestingSession

LIMIT_PER_WINDOW = int(LOGIN_RATE_LIMIT.split("/")[0])


@pytest.fixture
def rate_limited_client(client):
    limiter.reset()
    limiter.enabled = True
    yield client
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
def ip_throttle_enabled():
    with TestingSession() as db:
        row = db.get(AppSettings, 1)
        row.ip_throttle_enabled = True
        db.commit()


def _attempt_login(client):
    return client.post(
        "/api/v1/auth/login",
        data={"username": "nobody", "password": "wrong"},
    )


def test_login_allows_up_to_limit_then_returns_429(rate_limited_client):
    for _ in range(LIMIT_PER_WINDOW):
        response = _attempt_login(rate_limited_client)
        assert response.status_code == 401

    blocked = _attempt_login(rate_limited_client)

    assert blocked.status_code == 429


def test_login_returns_423_when_ip_throttle_enabled(client, ip_throttle_enabled):
    statuses = [_attempt_login(client).status_code for _ in range(LIMIT_PER_WINDOW + 3)]

    assert statuses[:LIMIT_PER_WINDOW] == [401] * LIMIT_PER_WINDOW
    assert all(code == 423 for code in statuses[LIMIT_PER_WINDOW:])


def test_login_skips_ip_throttle_when_disabled(client):
    statuses = [_attempt_login(client).status_code for _ in range(LIMIT_PER_WINDOW + 3)]

    assert all(code == 401 for code in statuses)
