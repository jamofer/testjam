"""Login endpoint rejects after exceeding the per-IP rate limit."""
import pytest

from testjam.core.rate_limit import LOGIN_RATE_LIMIT, limiter

LIMIT_PER_WINDOW = int(LOGIN_RATE_LIMIT.split("/")[0])


@pytest.fixture
def rate_limited_client(client):
    limiter.reset()
    limiter.enabled = True
    yield client
    limiter.enabled = False
    limiter.reset()


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


def test_login_succeeds_normally_when_limiter_disabled(client):
    for _ in range(LIMIT_PER_WINDOW + 3):
        response = _attempt_login(client)
        assert response.status_code == 401
